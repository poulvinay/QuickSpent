package org.example.quickspend;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.RemoteViews;

public class QuickSpendWidgetProvider extends AppWidgetProvider {
    private static final String PREFS = "quickspend_widget";

    public static void updateWidget(Context context, String income, String outgoing) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putString("income", income)
                .putString("outgoing", outgoing)
                .apply();
        AppWidgetManager manager = AppWidgetManager.getInstance(context);
        ComponentName provider = new ComponentName(context, QuickSpendWidgetProvider.class);
        int[] ids = manager.getAppWidgetIds(provider);
        for (int id : ids) {
            updateOne(context, manager, id);
        }
    }

    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] ids) {
        for (int id : ids) {
            updateOne(context, manager, id);
        }
    }

    @Override
    public void onAppWidgetOptionsChanged(
            Context context, AppWidgetManager manager, int appWidgetId, Bundle newOptions) {
        updateOne(context, manager, appWidgetId);
    }

    private static void updateOne(Context context, AppWidgetManager manager, int id) {
        RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.quickspend_widget);
        android.content.SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        views.setTextViewText(R.id.widget_income, prefs.getString("income", "₹0.00"));
        views.setTextViewText(R.id.widget_outgoing, prefs.getString("outgoing", "₹0.00"));
        views.setTextViewText(R.id.widget_income_vertical, prefs.getString("income", "₹0.00"));
        views.setTextViewText(R.id.widget_outgoing_vertical, prefs.getString("outgoing", "₹0.00"));

        Bundle options = manager.getAppWidgetOptions(id);
        int width = Math.max(
                options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH),
                options.getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_WIDTH));
        int height = Math.max(
                options.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT),
                options.getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT));
        boolean stackTotals = height > width;
        views.setViewVisibility(
                R.id.widget_totals_horizontal, stackTotals ? View.GONE : View.VISIBLE);
        views.setViewVisibility(
                R.id.widget_totals_vertical, stackTotals ? View.VISIBLE : View.GONE);

        Intent launch = new Intent(context, QuickSpendActivity.class);
        launch.putExtra(QuickSpendActivity.EXTRA_QUICK_ENTRY, true);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pending = PendingIntent.getActivity(
                context, 4101, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        views.setOnClickPendingIntent(R.id.widget_add, pending);
        views.setOnClickPendingIntent(R.id.widget_root, pending);
        manager.updateAppWidget(id, views);
    }
}
