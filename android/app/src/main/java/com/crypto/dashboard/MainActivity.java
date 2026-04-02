package com.crypto.dashboard;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.ConsoleMessage;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final String TAG = "CryptoDashboard";
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        Log.d(TAG, "MainActivity onCreate started");
        
        // Enable full screen (no title bar)
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN
        );
        
        setContentView(R.layout.activity_main);
        
        Log.d(TAG, "Layout set, initializing WebView");
        
        // Initialize WebView
        webView = findViewById(R.id.webview);
        
        if (webView == null) {
            Log.e(TAG, "WebView is null!");
            Toast.makeText(this, "WebView initialization failed", Toast.LENGTH_LONG).show();
            return;
        }
        
        Log.d(TAG, "WebView found, configuring settings");
        
        // Configure WebView settings
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);
        webSettings.setCacheMode(WebSettings.LOAD_DEFAULT);
        webSettings.setDatabaseEnabled(true);
        webSettings.setGeolocationEnabled(true);
        webSettings.setLoadWithOverviewMode(true);
        webSettings.setUseWideViewPort(true);
        webSettings.setBuiltInZoomControls(false);
        webSettings.setDisplayZoomControls(false);
        
        // Support mixed content (HTTP + HTTPS) for Android 5.0+
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
            webSettings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }
        
        Log.d(TAG, "WebView settings configured");
        
        // Set WebViewClient to handle page navigation
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                Log.d(TAG, "Page loaded: " + url);
                Toast.makeText(MainActivity.this, "Dashboard loaded!", Toast.LENGTH_SHORT).show();
            }
            
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                Log.e(TAG, "WebView error: " + errorCode + " - " + description + " at " + failingUrl);
                Toast.makeText(MainActivity.this, "Load error: " + description, Toast.LENGTH_LONG).show();
            }
        });
        
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage consoleMessage) {
                Log.d(TAG, "Console: " + consoleMessage.message() + " -- From line " 
                    + consoleMessage.lineNumber() + " of " + consoleMessage.sourceId());
                return true;
            }
        });
        
        // Load local PWA
        String pwaUrl = "file:///android_asset/www/index.html";
        Log.d(TAG, "Loading PWA: " + pwaUrl);
        webView.loadUrl(pwaUrl);
        
        Log.d(TAG, "MainActivity onCreate completed");
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
