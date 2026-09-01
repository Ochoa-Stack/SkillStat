def test_environment_sanity(app):
    """ Test trivial para validar que la fixture de la aplicación arranca correctamente y está usando la configuración de testing """
    assert app.config["TESTING"] is True
