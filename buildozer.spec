[app]
title = MoodTracker
package.name = moodtracker
package.domain = org.rybjuani
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf
source.exclude_dirs = __pycache__,.git,.github,bin,.buildozer
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.api = 31
android.minapi = 24
android.archs = arm64-v8a
android.permissions = INTERNET
presplash.color = #0f0f18

[buildozer]
log_level = 2
warn_on_root = 1
