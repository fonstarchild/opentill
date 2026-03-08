#[cfg(debug_assertions)]
use tauri::Manager;
use tauri_plugin_shell::ShellExt;

// Port the backend listens on — must match backend/main.py
const BACKEND_PORT: u16 = 47821;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_notification::init())
        .setup(|app| {
            // Spawn the bundled backend sidecar
            let sidecar = app.shell().sidecar("opentill-backend")?;
            let (_rx, _child) = sidecar
                .env("OPENTILL_PORT", BACKEND_PORT.to_string())
                .spawn()?;

            // Log sidecar output in debug builds
            #[cfg(debug_assertions)]
            tauri::async_runtime::spawn(async move {
                use tauri_plugin_shell::process::CommandEvent;
                while let Some(event) = _rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            let line = String::from_utf8_lossy(&line);
                            println!("[backend] {}", line.trim());
                        }
                        CommandEvent::Stderr(line) => {
                            let line = String::from_utf8_lossy(&line);
                            eprintln!("[backend:err] {}", line.trim());
                        }
                        _ => {}
                    }
                }
            });

            // Open devtools in debug mode
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![])
        .run(tauri::generate_context!())
        .expect("error while running opentill");
}
