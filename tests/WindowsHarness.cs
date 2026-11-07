using System;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using WebsiteApp;

internal static class IntegrationTests
{
    private static int checks;
    private static void Assert(bool condition, string name)
    {
        if (!condition) throw new Exception(name);
        Console.WriteLine("PASS: " + name);
        checks++;
    }

    [STAThread]
    private static int Main(string[] args)
    {
        try
        {
            Application.EnableVisualStyles();
            var config = new JavaScriptSerializer().Deserialize<AppConfig>(File.ReadAllText(args[0]));
            Assert(ExitProtection.Verify("salom🔒123", config.Password), "Python / .NET Unicode password match");
            Assert(!ExitProtection.Verify("wrong", config.Password), "Wrong password rejected");
            Assert(ExitProtection.Verify("", null), "Optional password");
            Assert(!ExitProtection.Verify("salom🔒123 ", config.Password), "Spaces preserved");
            Assert(!ExitProtection.Verify("x", new PasswordRecord { Salt = "invalid", Hash = "invalid", Iterations = 210000 }), "Malformed hash rejected");
            Assert(!MainForm.IsWebUrl("file:///C:/windows"), "Local file navigation blocked");
            Assert(!MainForm.IsWebUrl("https://user:pass@example.com"), "URL credentials blocked");
            Assert(MainForm.IsWebUrl(config.Url), "Web navigation accepted");
            using (var form = new MainForm(config))
            {
                Assert(form.FormBorderStyle == FormBorderStyle.None && !form.ControlBox,
                    "Fullscreen window has no title bar or window buttons");
                Assert(!form.MinimizeBox && !form.MaximizeBox, "Minimize and maximize controls disabled");
                Assert(form.Bounds == Screen.FromRectangle(form.Bounds).Bounds, "Window fills full monitor bounds");
                var wndProc = typeof(MainForm).GetMethod("WndProc", BindingFlags.Instance | BindingFlags.NonPublic);
                foreach (int command in new int[] { 0xF000, 0xF010, 0xF020, 0xF030, 0xF120 })
                {
                    var before = form.Bounds;
                    object[] parameters = { Message.Create(form.Handle, 0x0112, new IntPtr(command), IntPtr.Zero) };
                    wndProc.Invoke(form, parameters);
                    Assert(form.WindowState == FormWindowState.Normal && form.Bounds == before,
                        "Window size command blocked: " + command);
                }
                var onClosing = typeof(MainForm).GetMethod("OnFormClosing", BindingFlags.Instance | BindingFlags.NonPublic);
                var cancelled = new FormClosingEventArgs(CloseReason.UserClosing, false);
                TestDialog(form, onClosing, cancelled, false);
                Assert(cancelled.Cancel, "Wrong password and cancel keep main window open");
                var shutdown = new FormClosingEventArgs(CloseReason.WindowsShutDown, false);
                onClosing.Invoke(form, new object[] { shutdown });
                Assert(!shutdown.Cancel, "Windows shutdown allowed");
                var accepted = new FormClosingEventArgs(CloseReason.UserClosing, false);
                TestDialog(form, onClosing, accepted, true);
                Assert(!accepted.Cancel, "Correct password allows closing");
            }
            config.Password = null;
            using (var form = new MainForm(config))
            {
                var closing = new FormClosingEventArgs(CloseReason.UserClosing, false);
                typeof(MainForm).GetMethod("OnFormClosing", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(form, new object[] { closing });
                Assert(!closing.Cancel, "Unprotected application closes directly");
            }
            Console.WriteLine("ALL WINDOWS CHECKS PASSED: " + checks);
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine(error); return 1; }
    }

    private static void TestDialog(MainForm form, MethodInfo onClosing, FormClosingEventArgs args, bool correct)
    {
        Exception failure = null;
        bool started = false;
        DateTime deadline = DateTime.UtcNow.AddSeconds(20);
        using (var timer = new Timer { Interval = 100 })
        {
            timer.Tick += async delegate
            {
                if (started) return;
                foreach (Form open in Application.OpenForms)
                {
                    if (open.GetType().Name != "ExitDialog") continue;
                    started = true;
                    try
                    {
                        var input = (TextBox)open.GetType().GetField("input", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(open);
                        var button = (Button)open.GetType().GetField("submit", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(open);
                        var feedback = (Label)open.GetType().GetField("feedback", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(open);
                        input.Text = correct ? "salom🔒123" : "incorrect";
                        button.PerformClick();
                        while (DateTime.UtcNow < deadline && !open.IsDisposed && open.Visible && feedback.Text == "Tekshirilmoqda…")
                            await Task.Delay(100);
                        if (!correct)
                        {
                            Assert(feedback.Text.Contains("noto'g'ri"), "Wrong password shown in real dialog");
                            open.DialogResult = DialogResult.Cancel;
                            open.Close();
                        }
                        else if (!open.IsDisposed && open.Visible) throw new Exception("Correct password dialog did not close");
                    }
                    catch (Exception error) { failure = error; open.Close(); }
                    break;
                }
            };
            timer.Start();
            onClosing.Invoke(form, new object[] { args });
            timer.Stop();
        }
        if (failure != null) throw failure;
        Assert(started, "Password dialog opens");
    }
}
