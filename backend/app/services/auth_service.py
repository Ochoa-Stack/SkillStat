import secrets
import hashlib
import logging
from datetime import datetime, timezone, timedelta

from app.repositories.user_repository import UserRepository
from app.repositories.email_verification_token_repository import EmailVerificationTokenRepository
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.google_link_token_repository import GoogleLinkTokenRepository
from app.repositories.oauth_account_repository import OAuthAccountRepository
from app.utils.hash import hash_password, verify_password
from app.utils.security import generate_tokens
from app.utils.errors import AppError, ConflictError
import google.oauth2.id_token as google_id_token
import google.auth.transport.requests as google_requests

logger = logging.getLogger(__name__)

class AuthService:

    @classmethod
    def register(cls, data: dict) -> object:
        """ Crea una cuenta nueva y emite el token de verificación de correo.
        - Parámetros: data ya validado por UserRegistrationSchema (email, password, first_name, last_name).
        
        - Devuelve: (user, plain_token) donde plain_token es el token en texto plano que debe enviarse por correo; el hash nunca sale de esta capa.
        
        - Lanza: ConflictError si el correo ya está registrado. """
        if UserRepository.get_by_email(data["email"]):
            raise ConflictError("El correo ya está registrado.")

        user_data = dict(data)
        user_data["password_hash"] = hash_password(user_data.pop("password"))
        user_data["role"] = "REGISTERED"
        # Marcamos el instante de creación de contraseña para que el blocklist callback pueda invalidar sesiones anteriores si la contraseña cambia.
        user_data["password_changed_at"] = datetime.now(timezone.utc)

        user = UserRepository.create(user_data)

        plain_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        EmailVerificationTokenRepository.create({
            "user_id": user.id,
            "token_hash": token_hash,
            "expires_at": expires_at,
        })

        return user, plain_token

    @classmethod
    def login(cls, data: dict) -> tuple:
        """ Valida credenciales y genera tokens de acceso.
        - Parámetros: data ya validado por UserLoginSchema (email, password).
        
        - Devuelve: (user, tokens) donde tokens es el dict devuelto por generate_tokens, listo para que el controlador lo coloque en cookie.
        
        - Lanza: AppError con code UNAUTHORIZED si las credenciales son incorrectas o el correo no ha sido verificado. """
        user = UserRepository.get_by_email(data["email"])

        if not user or user.password_hash is None or not verify_password(data["password"], user.password_hash):
            raise AppError("Credenciales incorrectas.", code="UNAUTHORIZED", status_code=401)

        if user.email_verified_at is None:
            raise AppError(
                "Verifica tu correo antes de iniciar sesión.",
                code="EMAIL_NOT_VERIFIED",
                status_code=403,
            )

        tokens = generate_tokens(user_id=user.id, role=user.role)
        return user, tokens

    @classmethod
    def _validate_verification_token(cls, token: str) -> tuple:
        """ Valida un token de verificación sin mutar ningún estado.

        - Devuelve: (token_row, user) si el token es válido.

        - Lanza: AppError con el code y status_code correspondiente si el token no existe, ya fue usado, o expiró. Seguro para llamarse desde un GET ya que no escribe en base de datos. """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        token_row = EmailVerificationTokenRepository.get_by_token_hash(token_hash)

        if not token_row:
            raise AppError(
                "El enlace de verificación no es válido.",
                code="TOKEN_INVALID",
                status_code=404,
            )

        if token_row.used_at is not None:
            raise AppError(
                "Este correo ya fue verificado anteriormente.",
                code="TOKEN_ALREADY_USED",
                status_code=409,
            )

        now = datetime.now(timezone.utc)
        expires_aware = (
            token_row.expires_at.replace(tzinfo=timezone.utc)
            if token_row.expires_at.tzinfo is None
            else token_row.expires_at
        )
        if expires_aware < now:
            raise AppError(
                "El enlace expiró. Solicita uno nuevo.",
                code="TOKEN_EXPIRED",
                status_code=410,
            )

        user = UserRepository.get_by_id(token_row.user_id)
        return token_row, user

    @classmethod
    def verify_email_check(cls, token: str) -> dict:
        """Valida el token sin marcarlo como usado ni verificar la cuenta. Seguro para prefetch de escáneres de correo — no tiene efectos
        secundarios.

        - Devuelve: dict con {valid: True, email} si el token es válido.

        - Lanza: AppError si el token no es válido, ya fue usado, o expiró. """
        token_row, user = cls._validate_verification_token(token)
        return {"valid": True, "email": user.email if user else None}

    @classmethod
    def verify_email_confirm(cls, token: str) -> None:
        """Ejecuta la verificación real tras la confirmación explícita del usuario. Vuelve a validar el token para cubrir la ventana entre el GET y el clic (race condition o token consumido en paralelo). Si sigue siendo válido, muta el estado: marca email_verified_at en el usuario y used_at en el token.

        - Lanza: AppError si el token ya no es válido en el momento del POST. """
        token_row, user = cls._validate_verification_token(token)

        now = datetime.now(timezone.utc)
        if user:
            user.email_verified_at = now
            UserRepository.save(user)

        EmailVerificationTokenRepository.mark_as_used(token_row)

    @classmethod
    def resend_verification(cls, email: str) -> None:
        """ Invalida tokens anteriores y emite uno nuevo si el correo existe y no ha sido verificado. Diseñado para respuesta genérica (no revela si el correo existe): el controlador siempre devuelve 200 independientemente del resultado.

        - Devuelve: (plain_token, user_email) si se emitió un token nuevo, o (None, None) si el correo no existe o ya está verificado, en ambos casos el controlador responde igual.

        - Lanza: AppError si falla la creación del token en base de datos (propagado al logger del controlador, no al usuario final). """
        user = UserRepository.get_by_email(email)
        if not user or user.email_verified_at is not None:
            return None, None

        unused_tokens = EmailVerificationTokenRepository.get_unused_by_user_id(user.id)
        for t in unused_tokens:
            EmailVerificationTokenRepository.mark_as_used(t)

        plain_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        EmailVerificationTokenRepository.create({
            "user_id": user.id,
            "token_hash": token_hash,
            "expires_at": expires_at,
        })

        return plain_token, user.email

    @classmethod
    def forgot_password(cls, email: str) -> tuple:
        """Crea un token de recuperación de contraseña si el correo existe. Diseñado para respuesta genérica (no revela si el correo existe): el controlador siempre devuelve 200 independientemente del resultado.

        - Devuelve: (plain_token, user_email) si el usuario existe, o (None, None) si no existe, en ambos casos el controlador responde igual. """
        user = UserRepository.get_by_email(email)
        if not user:
            return None, None

        # El token en texto plano solo vive en memoria durante esta request; guardamos su hash SHA-256 en la base de datos, nunca el valor original.
        plain_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        PasswordResetTokenRepository.create({
            "user_id": user.id,
            "token_hash": token_hash,
            "expires_at": expires_at,
        })

        return plain_token, user.email

    @classmethod
    def reset_password(cls, token: str, new_password: str) -> None:
        """ Valida el token de recuperación y actualiza la contraseña del usuario. password_changed_at se actualiza en el mismo save() para invalidar todos los JWT emitidos antes de este momento; un atacante que hubiera robado un token activo queda bloqueado inmediatamente sin acción adicional.

        - Lanza: AppError si el token no es válido, ya fue usado, o expiró. AppError si el usuario asociado al token ya no existe. """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        token_row = PasswordResetTokenRepository.get_by_token_hash(token_hash)

        now = datetime.now(timezone.utc)
        expires_aware = (
            token_row.expires_at.replace(tzinfo=timezone.utc)
            if token_row and token_row.expires_at.tzinfo is None
            else (token_row.expires_at if token_row else None)
        )

        if (
            not token_row
            or token_row.used_at is not None
            or (expires_aware and expires_aware < now)
        ):
            raise AppError(
                "El enlace de recuperación no es válido o ya expiró.",
                code="INVALID_TOKEN",
                status_code=400,
            )

        user = UserRepository.get_by_id(token_row.user_id)
        if not user:
            raise AppError(
                "El usuario asociado a este token ya no existe.",
                code="NOT_FOUND",
                status_code=404,
            )

        # Actualizamos el hash de la contraseña con el mismo mecanismo bcrypt que usa el registro normal, no se reinventa ningún mecanismo de cifrado.
        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        UserRepository.save(user)

        # Invalidamos el token de inmediato para que no pueda reutilizarse.
        PasswordResetTokenRepository.mark_as_used(token_row)

    @classmethod
    def authenticate_with_google(cls, credential: str, google_client_id: str) -> tuple:
        """Verifica el token de Google y resuelve la cuenta del usuario. Tres casos posibles:
        1. OAuthAccount ya vinculado => autentica de inmediato, devuelve (user, tokens).
        2. User con el mismo email existe pero sin OAuthAccount => genera un
           GoogleLinkToken pendiente y lanza AppError(code='ACCOUNT_LINK_PENDING',
           status_code=200) con el link_token en el campo `detail` para que el
           controlador lo devuelva al frontend sin emitir sesión.
        3. Ni OAuthAccount ni User existen => crea cuenta nueva y autentica de
           inmediato, devuelve (user, tokens).

        Lanza:
        - AppError(TOKEN_INVALID, 401) si el token de Google no es válido.
        - AppError(EMAIL_NOT_VERIFIED, 401) si Google no marcó el email como verificado.
        - AppError(NOT_FOUND, 404) si el OAuthAccount existe pero el User fue eliminado.
        - AppError(ACCOUNT_LINK_PENDING, 200) si se requiere confirmación explícita. """
        from google.oauth2 import id_token as _google_id_token
        from google.auth.transport import requests as _google_requests

        try:
            idinfo = google_id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                google_client_id,
            )
        except ValueError:
            raise AppError(
                "El token de Google no es válido.",
                code="TOKEN_INVALID",
                status_code=401,
            )

        # Solo vinculamos automaticamente con una cuenta existente si Google ya verifico que el usuario controla ese correo; sin esto, alguien podria reclamar la cuenta de otra persona con solo conocer su email.
        email_verified = str(idinfo.get("email_verified", "")).lower() == "true"
        if not email_verified:
            raise AppError(
                "El correo de Google no está verificado.",
                code="EMAIL_NOT_VERIFIED",
                status_code=401,
            )

        google_user_id = idinfo["sub"]
        email = idinfo["email"].lower().strip()
        first_name = idinfo.get("given_name", "Usuario")
        last_name = idinfo.get("family_name", "Google")

        # Caso 1: ya existe un OAuthAccount para este google_user_id.
        oauth_account = OAuthAccountRepository.get_by_provider_identity("google", google_user_id)
        if oauth_account:
            user = UserRepository.get_by_id(oauth_account.user_id)
            if not user:
                raise AppError(
                    "La cuenta vinculada ya no existe.",
                    code="NOT_FOUND",
                    status_code=404,
                )
            tokens = generate_tokens(user_id=user.id, role=user.role)
            return user, tokens

        # Caso 2: existe User con ese email, pero sin OAuthAccount de Google. En lugar de vincular de inmediato, emitimos un token de confirmación para que el usuario apruebe explicitamente la vinculacion.
        existing_user = UserRepository.get_by_email(email)
        if existing_user:
            plain_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(plain_token.encode()).hexdigest()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

            GoogleLinkTokenRepository.create({
                "user_id": existing_user.id,
                "token_hash": token_hash,
                "google_user_id": google_user_id,
                "pending_email": email,
                "pending_first_name": first_name,
                "pending_last_name": last_name,
                "expires_at": expires_at,
            })

            raise AppError(
                "Ya existe una cuenta con ese correo. Confirma la vinculación.",
                code="ACCOUNT_LINK_PENDING",
                status_code=200,
                detail={"link_token": plain_token, "email": email},
            )

        # Caso 3: cuenta completamente nueva, sin User ni OAuthAccount. Sin cambio de comportamiento respecto al flujo previo.
        from datetime import datetime as _dt
        user = UserRepository.create({
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "role": "REGISTERED",
            "email_verified_at": datetime.now(timezone.utc),
        })
        OAuthAccountRepository.create({
            "user_id": user.id,
            "provider": "google",
            "provider_user_id": google_user_id,
        })
        tokens = generate_tokens(user_id=user.id, role=user.role)
        return user, tokens

    @classmethod
    def confirm_google_link(cls, link_token: str) -> tuple:
        """ Valida el token de vinculación pendiente y completa la vinculación. Mismo patrón de validación que _validate_verification_token: verifica existencia, no usado y no expirado. Si pasa, crea el OAuthAccount, marca el token como usado y devuelve (user, tokens) listos para que el controlador emita la sesión.

        Lanza:
        - AppError(TOKEN_INVALID, 404) si el token no existe.
        - AppError(TOKEN_ALREADY_USED, 409) si ya fue consumido.
        - AppError(TOKEN_EXPIRED, 410) si venció la ventana de 15 minutos.
        - AppError(NOT_FOUND, 404) si el User asociado fue eliminado. """
        token_hash = hashlib.sha256(link_token.encode()).hexdigest()
        token_row = GoogleLinkTokenRepository.get_by_token_hash(token_hash)

        if not token_row:
            raise AppError(
                "El enlace de vinculación no es válido.",
                code="TOKEN_INVALID",
                status_code=404,
            )

        if token_row.used_at is not None:
            raise AppError(
                "Este enlace de vinculación ya fue utilizado.",
                code="TOKEN_ALREADY_USED",
                status_code=409,
            )

        now = datetime.now(timezone.utc)
        expires_aware = (
            token_row.expires_at.replace(tzinfo=timezone.utc)
            if token_row.expires_at.tzinfo is None
            else token_row.expires_at
        )
        if expires_aware < now:
            raise AppError(
                "El enlace de vinculación expiró. Intenta iniciar sesión con Google de nuevo.",
                code="TOKEN_EXPIRED",
                status_code=410,
            )

        user = UserRepository.get_by_id(token_row.user_id)
        if not user:
            raise AppError(
                "El usuario asociado a este token ya no existe.",
                code="NOT_FOUND",
                status_code=404,
            )

        OAuthAccountRepository.create({
            "user_id": user.id,
            "provider": "google",
            "provider_user_id": token_row.google_user_id,
        })
        GoogleLinkTokenRepository.mark_as_used(token_row)

        tokens = generate_tokens(user_id=user.id, role=user.role)
        return user, tokens
