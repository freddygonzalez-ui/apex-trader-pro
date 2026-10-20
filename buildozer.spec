[app]

# (str) Title of your application
title = Apex Trader Pro

# (str) Package name
package.name = apextraderpro

# (str) Package domain (needed for android packaging)
package.domain = org.apextrader

# (list) Source files to include (let it empty to include all the files)
source.include_exts = py,png

# (list) Directory to load source from
source.dir = .

# (str) Application versioning
version = 1.0

# (list) Application requirements
# Añadidos certifi, urllib3, idna, charset-normalizer y openssl/openssl ya que 'requests' los requiere obligatoriamente para funcionar en Android.
requirements = python3,kivy,requests,urllib3,idna,charset-normalizer,certifi,openssl

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (str) Supported orientations (optional but good to specify)
# Android explicit API and SDK configurations to prevent build crashes
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (withcommand output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
