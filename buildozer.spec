[app]

title = QuickSpend
package.name = quickspend
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg
icon.filename = icon/finance-tracker-icon-square.png
presplash.filename = icon/finance-tracker-icon.png
android.presplash_color = #000000
android.add_src = android/src
android.add_resources = android/res
android.activity_class_name = org.example.quickspend.QuickSpendActivity
android.entrypoint = org.example.quickspend.QuickSpendActivity
android.minapi = 24
android.permissions = POST_NOTIFICATIONS
p4a.extra_args = --extra-manifest-application-xml '<receiver android:name="org.example.quickspend.QuickSpendWidgetProvider" android:exported="true" android:label="QuickSpend"><intent-filter><action android:name="android.appwidget.action.APPWIDGET_UPDATE"/></intent-filter><meta-data android:name="android.appwidget.provider" android:resource="@xml/quickspend_widget_info"/></receiver><service android:name="org.example.quickspend.QuickSpendTileService" android:exported="true" android:label="Add money" android:icon="@drawable/ic_add_money" android:permission="android.permission.BIND_QUICK_SETTINGS_TILE"><intent-filter><action android:name="android.service.quicksettings.action.QS_TILE"/></intent-filter></service>'

version = 1.0.0
requirements = python3,kivy

orientation = portrait
fullscreen = 0

p4a.branch = develop

[buildozer]

log_level = 2
warn_on_root = 1
