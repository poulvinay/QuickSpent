# QuickSpend

QuickSpend is an offline-first money tracker built with Python, Kivy, and KivyMD. It records income and spending in INR, groups transactions by category, and stores everything on the device in SQLite. The Android build also offers launcher and system shortcuts for opening the transaction flow.

## How to use the app

### Home

The home screen shows this calendar month's income and money out, plus the six most recently recorded transactions. Select **Add money** to start a transaction, or **Expense history** to browse and manage saved transactions. The settings menu (⋮) includes the monthly spending limit, category creation, and Android quick access options.

### Record money

1. Enter an amount in INR. Amounts are rounded to two decimal places; zero and negative values are rejected.
2. Optionally add a note.
3. Choose a category under **Money out** or **Money in**. This saves the transaction and returns to Home.

The app starts with these categories:

| Money in | Money out |
| --- | --- |
| Salary, Loaned | Food, Transport, Shopping, Bills, Health, Other |

Use **Add category** in the settings menu or category picker to add a category and choose its direction. Category names must be unique (ignoring letter case). Transactions inherit their direction from the selected category.

### History

History opens on the current month. Use the **Month** menu to choose the current month or a month with saved transactions, then use **Day** to narrow the list to one calendar day or return to **All days**. Up to 300 matching transactions are shown, newest first. Each row shows the direction, category, amount, date/time, and optional note. **Edit** changes the amount, category, or note; **Delete** removes the transaction after confirmation.

### Monthly spending limit

Choose **Monthly spending limit** from Home's settings menu and enter a positive amount in INR. QuickSpend checks the month's total Money out after each outgoing transaction. When that total reaches or exceeds the limit, it displays an in-app alert and, on Android when notifications are allowed, a system notification. The limit is saved locally and checked against each calendar month. Choose **Disable** in the limit dialog to turn it off.

## Android quick access

Choose **Shortcuts** from the settings menu to request an Android entry point:

- **Home screen widget** shows this month's income and money out. Tapping it opens amount entry. Android or the launcher may ask before placing it.
- **Pinned Add money shortcut** adds a separate launcher icon that opens amount entry, subject to launcher support and confirmation.
- **Lockscreen / heads-up notification** posts a QuickSpend notification with an **Add money** action. Android notification permission and lock screen settings control its display. The notification does not show transaction amounts.
- **Quick Settings tile** requests an **Add money** tile on Android 13 and later. On earlier supported Android versions, add QuickSpend from the Quick Settings edit screen.

Android apps cannot add a button to the system navigation bar at the bottom of the screen. The Quick Settings tile provides access from the swipe-down panel instead.

These features are implemented in `android/` and registered through `buildozer.spec`. The app's minimum Android API level is 24. Some shortcuts depend on Android version and launcher support; Android controls notification visibility and widget placement.

## Run on desktop

Use Python 3.10 or later. From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "kivy==2.3.1" "kivymd==2.0.0"
python main.py
```

Desktop runs use the light teal theme. Android shortcuts and widgets are only available in a packaged Android build.

## Build for Android

Buildozer and its Android SDK/NDK dependencies are required. On Linux or WSL2, build a debug APK with:

```bash
buildozer -v android debug
```

The Python requirements, Android API level, Java sources, and Android resources are configured in `buildozer.spec`. If you change its `requirements`, run `buildozer android clean` before rebuilding so Buildozer downloads the updated packages.

## Data and appearance

The database is `expenses.db` in the app's private data directory. Transaction amounts are stored as integer paise to avoid floating-point rounding; the currency is INR. Categories, transaction notes, the monthly limit, and transactions remain on the device. Existing databases are upgraded to include category direction; pre-existing categories are treated as Money out.

The interface uses KivyMD 2.0 Material 3 components. On Android 12 and later, the app uses wallpaper-based Material You colours; otherwise it uses a teal seed colour. The app follows Android's light or dark setting, while income remains green and money out remains red. Desktop runs use the light theme.
