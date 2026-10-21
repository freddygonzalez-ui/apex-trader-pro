[app]

# (str) Title of your application
title = Apex Trader Pro

# (str) Package name
package.name = apextraderpro

# (str) Package domain (needed for android packaging)
package.domain = org.apextrader

# (list) Source files to include (let it empty to include all the files)
source.include_exts = py,png

# (str) Icon of the application
icon.filename = %(source.dir)s/logo.png

# (list) Directory to load source from
source.dir = .

# (str) Application versioning
version = 1.0

# (list) Application requirements
requirements = python3,kivy,setuptools,requests,urllib3<2,idna,charset-normalizer,certifi,openssl

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# Android explicit API and SDK configurations
android.api = 34
android.minapi = 21
android.ndk = 28c
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 1

# (int) Display warning if buildozer is run as root
warn_on_root = 1
