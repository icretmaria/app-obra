[app]
title = Fotos Obra
package.name = fotos_obra
package.domain = org.obra
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# BIBLIOTECAS REQUISITADAS PELO SISTEMA
requirements = python3,kivy==2.3.0,plyer,reportlab==4.1.0,pillow==10.2.0

orientation = portrait

# PERMISSÕES NATIVAS DO ANDROID (CRÍTICO PARA FUNCIONAMENTO EM CAMPO)
android.permissions = CAMERA, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.private_storage = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
