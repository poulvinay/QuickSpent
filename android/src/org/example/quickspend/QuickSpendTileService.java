package org.example.quickspend;

import android.content.Intent;
import android.service.quicksettings.Tile;
import android.service.quicksettings.TileService;

public class QuickSpendTileService extends TileService {
    @Override
    public void onStartListening() {
        super.onStartListening();
        Tile tile = getQsTile();
        if (tile != null) {
            tile.setLabel("Add money");
            tile.setState(Tile.STATE_INACTIVE);
            tile.updateTile();
        }
    }

    @Override
    public void onClick() {
        super.onClick();
        Intent launch = new Intent(this, QuickSpendActivity.class);
        launch.putExtra(QuickSpendActivity.EXTRA_QUICK_ENTRY, true);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        if (isLocked()) {
            unlockAndRun(new Runnable() {
                @Override
                public void run() {
                    startActivity(launch);
                }
            });
        } else {
            startActivityAndCollapse(launch);
        }
    }
}
