package org.example.quickspend;

import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.RemoteInput;
import android.app.StatusBarManager;
import android.appwidget.AppWidgetManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ShortcutInfo;
import android.content.pm.ShortcutManager;
import android.content.res.Configuration;
import android.graphics.drawable.Icon;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.os.Build;
import android.widget.Toast;
import java.util.function.Consumer;

public class QuickSpendBridge {
    private static final String CHANNEL_ID = "quickspend_quick_add_v2";
    private static final String BUDGET_CHANNEL_ID = "quickspend_budget_alerts";
    private static final int NOTIFICATION_ID = 4102;
    private static final int BUDGET_NOTIFICATION_ID = 4103;
    private static volatile String pendingSpendingLimitMessage;

    private static Intent quickEntryIntent(Context context) {
        Intent intent = new Intent(context, QuickSpendActivity.class);
        intent.setAction(Intent.ACTION_MAIN);
        intent.addCategory(Intent.CATEGORY_LAUNCHER);
        intent.putExtra(QuickSpendActivity.EXTRA_QUICK_ENTRY, true);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        return intent;
    }

    public static void updateWidget(Context context, String income, String outgoing) {
        QuickSpendWidgetProvider.updateWidget(context, income, outgoing);
    }

    public static boolean isNightMode(Context context) {
        int nightMode = context.getResources().getConfiguration().uiMode
                & Configuration.UI_MODE_NIGHT_MASK;
        return nightMode == Configuration.UI_MODE_NIGHT_YES;
    }

    public static boolean pinWidget(Activity activity) {
        if (Build.VERSION.SDK_INT < 26) {
            Toast.makeText(activity, "Add QuickSpend from your home screen's widget list.", Toast.LENGTH_LONG).show();
            return false;
        }
        AppWidgetManager manager = AppWidgetManager.getInstance(activity);
        if (!manager.isRequestPinAppWidgetSupported()) {
            return false;
        }
        return manager.requestPinAppWidget(
                new ComponentName(activity, QuickSpendWidgetProvider.class), null, null);
    }

    public static boolean pinAddMoneyShortcut(Activity activity) {
        if (Build.VERSION.SDK_INT < 26) {
            Toast.makeText(activity, "Use the Add money item in the app menu.", Toast.LENGTH_LONG).show();
            return false;
        }
        ShortcutManager manager = activity.getSystemService(ShortcutManager.class);
        if (manager == null || !manager.isRequestPinShortcutSupported()) {
            return false;
        }
        Intent intent = quickEntryIntent(activity);
        ShortcutInfo shortcut = new ShortcutInfo.Builder(activity, "quickspend_add_money")
                .setShortLabel("Add money")
                .setLongLabel("Record money in or out")
                .setIcon(Icon.createWithResource(activity, R.drawable.ic_add_money_shortcut))
                .setIntent(intent)
                .build();
        return manager.requestPinShortcut(shortcut, null);
    }

    public static void showQuickAccessNotification(Activity activity) {
        if (Build.VERSION.SDK_INT >= 33
                && activity.checkSelfPermission("android.permission.POST_NOTIFICATIONS")
                != PackageManager.PERMISSION_GRANTED) {
            activity.requestPermissions(
                    new String[]{"android.permission.POST_NOTIFICATIONS"}, 4102);
            Toast.makeText(activity, "Allow notifications, then tap this option again.", Toast.LENGTH_LONG).show();
            return;
        }

        NotificationManager manager = activity.getSystemService(NotificationManager.class);
        if (Build.VERSION.SDK_INT >= 26 && manager.getNotificationChannel(CHANNEL_ID) == null) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "Quick add", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Optional shortcut to open QuickSpend entry");
            channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
            channel.setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION),
                    new AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_NOTIFICATION)
                            .build());
            channel.enableVibration(true);
            manager.createNotificationChannel(channel);
        }

        Intent launch = quickEntryIntent(activity);
        PendingIntent contentPending = PendingIntent.getActivity(
                activity, NOTIFICATION_ID, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        PendingIntent replyPending = PendingIntent.getActivity(
                activity, NOTIFICATION_ID + 1, launch,
                PendingIntent.FLAG_UPDATE_CURRENT
                        | (Build.VERSION.SDK_INT >= 31 ? PendingIntent.FLAG_MUTABLE : 0));
        RemoteInput amountInput = new RemoteInput.Builder(QuickSpendActivity.REMOTE_AMOUNT)
                .setLabel("Enter amount, then submit")
                .build();
        Notification.Action addMoneyAction = new Notification.Action.Builder(
                android.R.drawable.ic_input_add, "Add money", replyPending)
                .addRemoteInput(amountInput)
                .setAllowGeneratedReplies(false)
                .build();
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(activity, CHANNEL_ID)
                : new Notification.Builder(activity);
        Notification publicVersion = new Notification.Builder(activity)
                .setSmallIcon(R.drawable.ic_add_money)
                .setContentTitle("QuickSpend")
                .setContentText("Enter an amount to record money")
                .setCategory(Notification.CATEGORY_MESSAGE)
                .setPriority(Notification.PRIORITY_HIGH)
                .addAction(addMoneyAction)
                .build();
        Notification notification = builder
                .setSmallIcon(R.drawable.ic_add_money)
                .setContentTitle("QuickSpend")
                .setContentText("Reply with an amount to record money")
                .setCategory(Notification.CATEGORY_MESSAGE)
                .setPriority(Notification.PRIORITY_HIGH)
                .setDefaults(Notification.DEFAULT_SOUND | Notification.DEFAULT_VIBRATE)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setPublicVersion(publicVersion)
                .setContentIntent(contentPending)
                .addAction(addMoneyAction)
                .setAutoCancel(true)
                .build();
        manager.notify(NOTIFICATION_ID, notification);
    }

    public static void showSpendingLimitNotification(Activity activity, String message) {
        if (Build.VERSION.SDK_INT >= 33
                && activity.checkSelfPermission("android.permission.POST_NOTIFICATIONS")
                != PackageManager.PERMISSION_GRANTED) {
            pendingSpendingLimitMessage = message;
            activity.requestPermissions(
                    new String[]{"android.permission.POST_NOTIFICATIONS"}, BUDGET_NOTIFICATION_ID);
            return;
        }

        NotificationManager manager = activity.getSystemService(NotificationManager.class);
        if (Build.VERSION.SDK_INT >= 26 && manager.getNotificationChannel(BUDGET_CHANNEL_ID) == null) {
            NotificationChannel channel = new NotificationChannel(
                    BUDGET_CHANNEL_ID, "Spending limit alerts", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Alerts when monthly spending reaches its limit");
            channel.setLockscreenVisibility(Notification.VISIBILITY_PRIVATE);
            manager.createNotificationChannel(channel);
        }

        Intent launch = new Intent(activity, QuickSpendActivity.class);
        launch.setAction(Intent.ACTION_MAIN);
        launch.addCategory(Intent.CATEGORY_LAUNCHER);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent contentPending = PendingIntent.getActivity(
                activity, BUDGET_NOTIFICATION_ID, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(activity, BUDGET_CHANNEL_ID)
                : new Notification.Builder(activity);
        Notification notification = builder
                .setSmallIcon(R.drawable.ic_add_money)
                .setContentTitle("QuickSpend spending limit")
                .setContentText("Your monthly spending limit has been reached.")
                .setStyle(new Notification.BigTextStyle().bigText(message))
                .setCategory(Notification.CATEGORY_REMINDER)
                .setPriority(Notification.PRIORITY_HIGH)
                .setVisibility(Notification.VISIBILITY_PRIVATE)
                .setContentIntent(contentPending)
                .setAutoCancel(true)
                .build();
        manager.notify(BUDGET_NOTIFICATION_ID, notification);
    }

    public static void onNotificationPermissionResult(
            Activity activity, int requestCode, int[] grantResults) {
        if (requestCode != BUDGET_NOTIFICATION_ID) return;
        String message = pendingSpendingLimitMessage;
        pendingSpendingLimitMessage = null;
        if (message != null && grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            showSpendingLimitNotification(activity, message);
        }
    }

    public static void requestQuickSettingsTile(Activity activity) {
        if (Build.VERSION.SDK_INT >= 33) {
            StatusBarManager statusBar = activity.getSystemService(StatusBarManager.class);
            if (statusBar != null) {
                statusBar.requestAddTileService(
                        new ComponentName(activity, QuickSpendTileService.class),
                        "Add money",
                        Icon.createWithResource(activity, R.drawable.ic_add_money),
                        activity.getMainExecutor(),
                        new Consumer<Integer>() {
                            @Override
                            public void accept(Integer result) { }
                        });
            }
        } else {
            Toast.makeText(activity,
                    "Open Quick Settings, choose Edit, then add QuickSpend.",
                    Toast.LENGTH_LONG).show();
        }
    }
}
