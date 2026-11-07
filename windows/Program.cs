using System;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace WebsiteApp
{
    public sealed class AppConfig
    {
        public string Name { get; set; }
        public string Url { get; set; }
        public string Id { get; set; }
        public PasswordRecord Password { get; set; }
    }

    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            try
            {
                AppConfig config;
                using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("app.json"))
                using (var reader = new StreamReader(stream))
                    config = new JavaScriptSerializer().Deserialize<AppConfig>(reader.ReadToEnd());
                if (config == null || !MainForm.IsWebUrl(config.Url)) throw new InvalidDataException();
                Application.Run(new MainForm(config));
            }
            catch (Exception)
            {
                MessageBox.Show("Dastur ishga tushmadi. .NET Framework 4.8 va Microsoft Edge WebView2 Runtime o'rnatilganini tekshiring.",
                    "Ishga tushirish xatosi", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }

    internal sealed class MainForm : Form
    {
        private readonly AppConfig config;
        private readonly WebView2 browser;
        private readonly ToolStripStatusLabel status;
        private readonly Timer themeTimer;
        private readonly string themeScript;
        private AppTheme theme = new AppTheme(Color.White, false);
        private bool readingTheme;
        private bool pageReady;
        private bool exitAuthorized;
        private bool exitDialogOpen;

        public MainForm(AppConfig appConfig)
        {
            config = appConfig;
            Text = config.Name;
            using (var iconStream = Assembly.GetExecutingAssembly().GetManifestResourceStream("app.ico"))
            {
                if (iconStream != null)
                    using (var icon = new Icon(iconStream, new Size(32, 32))) Icon = (Icon)icon.Clone();
            }
            using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("theme.js"))
            {
                if (stream != null)
                    using (var reader = new StreamReader(stream)) themeScript = reader.ReadToEnd();
            }
            // Sarlavha, ramka va o'lchamni boshqarish tugmalarisiz to'liq ekran.
            FormBorderStyle = FormBorderStyle.None;
            ControlBox = false;
            MinimizeBox = false;
            MaximizeBox = false;
            StartPosition = FormStartPosition.Manual;
            Bounds = Screen.FromPoint(Cursor.Position).Bounds;
            Font = new Font("Segoe UI", 10);
            var toolbar = new ToolStrip { GripStyle = ToolStripGripStyle.Hidden, Padding = new Padding(6) };
            var back = new ToolStripButton("← Orqaga");
            var home = new ToolStripButton("Bosh sahifa");
            var reload = new ToolStripButton("Yangilash");
            var close = new ToolStripButton("Chiqish") { Alignment = ToolStripItemAlignment.Right };
            back.Click += delegate { if (browser.CoreWebView2 != null && browser.CanGoBack) browser.GoBack(); };
            home.Click += delegate { if (browser.CoreWebView2 != null) browser.CoreWebView2.Navigate(config.Url); };
            reload.Click += delegate { if (browser.CoreWebView2 != null) browser.Reload(); };
            close.Click += delegate { Close(); };
            toolbar.Items.AddRange(new ToolStripItem[] { back, home, reload, close });
            var strip = new StatusStrip();
            status = new ToolStripStatusLabel("Sayt yuklanmoqda…") { Spring = true, TextAlign = ContentAlignment.MiddleLeft };
            strip.Items.Add(status);
            browser = new WebView2 { Dock = DockStyle.Fill };
            Controls.Add(browser);
            Controls.Add(toolbar);
            Controls.Add(strip);
            themeTimer = new Timer { Interval = 800 };
            themeTimer.Tick += async delegate { await RefreshTheme(); };
            HandleCreated += delegate { theme.ApplyTitleBar(this); };
            Load += delegate { FillCurrentScreen(); };
            Shown += async delegate { await InitializeBrowser(); };
        }

        private void FillCurrentScreen()
        {
            if (IsDisposed || Disposing) return;
            // Bounds ish maydonidan farqli ravishda taskbar joyini ham qamrab oladi.
            Bounds = Screen.FromControl(this).Bounds;
        }

        protected override void WndProc(ref Message message)
        {
            const int WM_SYSCOMMAND = 0x0112;
            const int WM_DISPLAYCHANGE = 0x007E;
            if (message.Msg == WM_SYSCOMMAND)
            {
                long command = message.WParam.ToInt64() & 0xFFF0;
                // Faqat shu oynaning ko'chirish/kichraytirish/o'lcham buyruqlari bloklanadi.
                // SC_CLOSE odatdagi parol tekshiruviga o'tadi.
                if (command == 0xF000 || command == 0xF010 || command == 0xF020 ||
                    command == 0xF030 || command == 0xF120)
                {
                    message.Result = IntPtr.Zero;
                    return;
                }
            }
            base.WndProc(ref message);
            if (message.Msg == WM_DISPLAYCHANGE && IsHandleCreated && !IsDisposed && !Disposing)
                BeginInvoke(new Action(FillCurrentScreen));
        }

        public static bool IsWebUrl(string value)
        {
            Uri uri;
            return Uri.TryCreate(value, UriKind.Absolute, out uri) &&
                (uri.Scheme == Uri.UriSchemeHttps || uri.Scheme == Uri.UriSchemeHttp) &&
                !String.IsNullOrEmpty(uri.Host) && String.IsNullOrEmpty(uri.UserInfo);
        }

        private async Task InitializeBrowser()
        {
            try
            {
                string data = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "ExeCreator", config.Id, "BrowserData");
                var environment = await CoreWebView2Environment.CreateAsync(null, data);
                if (IsDisposed) return;
                await browser.EnsureCoreWebView2Async(environment);
                if (IsDisposed || Disposing) return;
                browser.CoreWebView2.Settings.AreDevToolsEnabled = false;
                browser.CoreWebView2.Settings.AreHostObjectsAllowed = false;
                browser.CoreWebView2.Settings.IsWebMessageEnabled = false;
                browser.CoreWebView2.Settings.AreDefaultContextMenusEnabled = false;
                browser.CoreWebView2.NavigationStarting += delegate(object sender, CoreWebView2NavigationStartingEventArgs e)
                {
                    if (!IsWebUrl(e.Uri)) { e.Cancel = true; status.Text = "Faqat http/https havolalar ochiladi."; }
                    else { pageReady = false; status.Text = "Yuklanmoqda…"; }
                };
                browser.CoreWebView2.NavigationCompleted += async delegate(object sender, CoreWebView2NavigationCompletedEventArgs e)
                {
                    pageReady = e.IsSuccess;
                    status.Text = e.IsSuccess ? "Tayyor" : "Sayt ochilmadi: " + e.WebErrorStatus + ". Internetni tekshiring va Yangilash tugmasini bosing.";
                    if (e.IsSuccess) await RefreshTheme();
                };
                // Popup ichidagi havolani ham shu himoyalangan oynada ochish.
                browser.CoreWebView2.NewWindowRequested += delegate(object sender, CoreWebView2NewWindowRequestedEventArgs e)
                {
                    e.Handled = true;
                    if (e.IsUserInitiated && IsWebUrl(e.Uri)) browser.CoreWebView2.Navigate(e.Uri);
                };
                browser.CoreWebView2.WindowCloseRequested += delegate { Close(); };
                themeTimer.Start();
                browser.CoreWebView2.Navigate(config.Url);
            }
            catch (Exception)
            {
                if (IsDisposed || Disposing) return;
                status.Text = "WebView2 ishga tushmadi.";
                MessageBox.Show(this,
                    "Microsoft Edge WebView2 Runtime kerak. O'rnatuvchini qayta ishga tushiring yoki https://developer.microsoft.com/microsoft-edge/webview2/ manzilidan Runtime o'rnating.",
                    config.Name, MessageBoxButtons.OK, MessageBoxIcon.Information);
                // Brauzer ochilmagan bo'lsa foydalanuvchini bo'sh oynada qamab qo'ymaslik.
                exitAuthorized = true;
            }
        }

        private async Task RefreshTheme()
        {
            if (readingTheme || !pageReady || IsDisposed || Disposing || WindowState == FormWindowState.Minimized ||
                browser.CoreWebView2 == null || String.IsNullOrEmpty(themeScript)) return;
            readingTheme = true;
            try
            {
                string value = await browser.CoreWebView2.ExecuteScriptAsync(themeScript);
                if (IsDisposed || Disposing || !pageReady) return;
                var snapshot = new JavaScriptSerializer().Deserialize<ThemeSnapshot>(value);
                var next = AppTheme.FromSnapshot(snapshot);
                if (next == null || (next.Background == theme.Background && next.IsDark == theme.IsDark)) return;
                theme = next;
                // Brauzer sahifasiga tegmasdan faqat Windows oynasi elementlarini bo'yash.
                BackColor = theme.Background;
                foreach (Control control in Controls)
                    if (control != browser) theme.Apply(control);
                browser.DefaultBackgroundColor = theme.Background;
                theme.ApplyTitleBar(this);
                foreach (Form owned in OwnedForms)
                {
                    var dialog = owned as ExitDialog;
                    if (dialog != null) dialog.ApplyTheme(theme);
                }
            }
            catch (InvalidOperationException) { }
            catch (ArgumentException) { }
            catch (System.Runtime.InteropServices.COMException) { }
            finally { readingTheme = false; }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            // Windows shutdown va administrator orqali majburiy tugatishga qarshilik yo'q.
            if (e.CloseReason == CloseReason.UserClosing && config.Password != null && !exitAuthorized)
            {
                e.Cancel = true;
                if (!exitDialogOpen)
                {
                    exitDialogOpen = true;
                    using (var dialog = new ExitDialog(config.Password, theme))
                    {
                        if (dialog.ShowDialog(this) == DialogResult.OK)
                        {
                            exitAuthorized = true;
                            e.Cancel = false;
                        }
                    }
                    exitDialogOpen = false;
                }
            }
            base.OnFormClosing(e);
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                if (themeTimer != null) { themeTimer.Stop(); themeTimer.Dispose(); }
                if (browser != null) browser.Dispose();
            }
            base.Dispose(disposing);
        }
    }

    internal sealed class ExitDialog : Form
    {
        private readonly TextBox input;
        private readonly Button submit;
        private readonly Label feedback;
        private readonly PasswordRecord record;
        private bool checking;

        public ExitDialog(PasswordRecord password, AppTheme theme)
        {
            record = password;
            Text = "Chiqish uchun parol";
            ClientSize = new Size(410, 205);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterParent;
            MaximizeBox = false;
            MinimizeBox = false;
            ShowInTaskbar = false;
            Font = new Font("Segoe UI", 10);
            var label = new Label { Text = "Dasturni yopish uchun parolni kiriting:", Left = 22, Top = 20, AutoSize = true };
            // 128 Unicode belgisi UTF-16 da 256 code unit bo'lishi mumkin.
            input = new TextBox { Left = 22, Top = 55, Width = 365, UseSystemPasswordChar = true, MaxLength = 256 };
            feedback = new Label { Left = 22, Top = 90, Width = 365, Height = 38, ForeColor = Color.Firebrick };
            submit = new Button { Text = "Chiqish", Left = 267, Top = 145, Width = 120, Height = 34 };
            var cancel = new Button { Text = "Bekor qilish", Left = 137, Top = 145, Width = 120, Height = 34, DialogResult = DialogResult.Cancel };
            submit.Click += async delegate { await CheckPassword(); };
            AcceptButton = submit;
            CancelButton = cancel;
            Controls.AddRange(new Control[] { label, input, feedback, submit, cancel });
            ApplyTheme(theme);
            Shown += delegate { ApplyTheme(theme); input.Focus(); };
        }

        public void ApplyTheme(AppTheme theme)
        {
            theme.Apply(this);
            feedback.ForeColor = theme.IsDark ? Color.FromArgb(255, 145, 145) : Color.Firebrick;
            theme.ApplyTitleBar(this);
        }

        private async Task CheckPassword()
        {
            if (checking) return;
            checking = true;
            submit.Enabled = false;
            input.Enabled = false;
            feedback.Text = "Tekshirilmoqda…";
            string candidate = input.Text;
            bool valid = await Task.Run(() => ExitProtection.Verify(candidate, record));
            candidate = null;
            if (IsDisposed || !Visible) return;
            if (valid) { DialogResult = DialogResult.OK; Close(); return; }
            feedback.Text = "Parol noto'g'ri. Qayta urinib ko'ring.";
            input.Clear();
            await Task.Delay(1000);
            if (IsDisposed || !Visible) return;
            checking = false;
            submit.Enabled = true;
            input.Enabled = true;
            input.Focus();
        }
    }
}
