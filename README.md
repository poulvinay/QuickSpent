# QuickSpend

QuickSpend is an offline-first Kivy money tracker for Android with a Material Design 3 interface built on KivyMD. It records money In or Out using typed categories, stores data locally in SQLite, and provides Android shortcuts to open the amount-entry screen.

## Look and feel

- Material 3 components from KivyMD 2.0: top app bars, filled and tonal buttons, outlined text fields, dialogs, menus, and a date picker for history.
- Material You: on Android 12+ the colours follow the wallpaper. Elsewhere the app uses a scheme generated from QuickSpend teal.
- Light and dark themes follow the phone's system setting, including switches made while the app is open.
- Money in stays green and money out stays red in every theme.
- The home screen widget uses the same colours, follows dark mode, and on Android 12+ uses the wallpaper colours and the launcher's corner radius.

## Money tracking

- Record money in or out with a two-step amount → category flow.
- Salary and Loaned are seeded as In categories; Food, Transport, Shopping, Bills, Health, and Other are Out categories.
- Choose In or Out when creating a category.
- Today's in/out totals and transaction cards use green for money in and red for money out.
- **Monthly spending limit:** set a budget from the home screen settings menu. QuickSpend alerts you when monthly money out reaches the limit; the limit is stored on-device and resets against each new calendar month.
- Edit or delete saved transactions from history.
- Existing databases are upgraded with a category direction field; existing categories are treated as Out.

## Android quick access

Open **Shortcuts and widgets** in the app for these Android entry points:

- **Home screen widget:** shows today's In and Out totals and opens amount entry when tapped. Android asks before placing it.
- **Pinned Add money shortcut:** adds a separate launcher icon that opens amount entry. The launcher asks before pinning it.
- **Lock screen / heads-up notification:** posts a private QuickSpend notification with an **Add money** action. Android and the user's notification settings control whether it appears on the lock screen or as a heads-up popup. It does not expose transaction amounts there.
- **Quick Settings tile:** asks the user to add an **Add money** tile to the swipe-down Quick Settings panel. On older supported Android versions, add it from the Quick Settings edit screen.

Android apps cannot add their own button to the system's bottom navigation bar. The Quick Settings tile is the supported system shortcut in the swipe-down panel. Lockscreen and heads-up notification display is controlled by Android and may differ by device or user settings.

These Android features use the Java integration and resources under `android/`, registered through `buildozer.spec`. The minimum Android API is 24 for the Quick Settings tile.

## Run on desktop

Use Python 3.10+ with Kivy and KivyMD:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "kivy==2.3.1" "kivymd==2.0.0"
python main.py
```

The desktop build always uses the light teal theme.

Android quick access controls are only available in the packaged Android app.

## Android packaging

Buildozer with its Android SDK/NDK dependencies is required on Linux or WSL2:

```bash
buildozer -v android debug
```

If you change `requirements` in `buildozer.spec`, run `buildozer android clean` first, because Buildozer keeps packages it has already downloaded.

The app icon source is `icon/finance-tracker-icon.png`. The local database is stored in the app's private data directory as `expenses.db`; amounts are stored as integer paise to avoid floating point rounding. Data stays on the device.
