package org.example.quickspend;

import android.content.Intent;
import android.content.res.Configuration;
import android.app.RemoteInput;
import android.os.Bundle;
import org.kivy.android.PythonActivity;

public class QuickSpendActivity extends PythonActivity {
    public static final String EXTRA_QUICK_ENTRY = "org.example.quickspend.QUICK_ENTRY";
    public static final String EXTRA_AMOUNT = "org.example.quickspend.AMOUNT";
    public static final String REMOTE_AMOUNT = "org.example.quickspend.REMOTE_AMOUNT";
    private static volatile boolean quickEntryRequested = false;
    private static volatile String pendingAmount = "";
    private static volatile boolean configurationChanged = false;

    private static void captureQuickEntry(Intent intent) {
        if (intent != null && intent.getBooleanExtra(EXTRA_QUICK_ENTRY, false)) {
            quickEntryRequested = true;
        }
        if (intent != null) {
            String amount = intent.getStringExtra(EXTRA_AMOUNT);
            if (amount == null) {
                Bundle results = RemoteInput.getResultsFromIntent(intent);
                if (results != null) {
                    CharSequence reply = results.getCharSequence(REMOTE_AMOUNT);
                    amount = reply == null ? null : reply.toString();
                }
            }
            if (amount != null) {
                pendingAmount = amount.trim();
                quickEntryRequested = true;
            }
        }
    }

    @Override
    protected void onCreate(Bundle state) {
        captureQuickEntry(getIntent());
        super.onCreate(state);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        captureQuickEntry(intent);
    }

    // The activity handles uiMode changes itself, so a dark mode switch arrives
    // here instead of recreating it; Python polls the flag and restyles.
    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        configurationChanged = true;
    }

    public static boolean consumeConfigurationChange() {
        boolean changed = configurationChanged;
        configurationChanged = false;
        return changed;
    }

    public static boolean consumeQuickEntryRequest() {
        boolean requested = quickEntryRequested;
        quickEntryRequested = false;
        return requested;
    }

    public static String consumeQuickEntryAmount() {
        String amount = pendingAmount;
        pendingAmount = "";
        return amount;
    }
}
