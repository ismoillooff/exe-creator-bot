using System;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.WinForms;
using WebsiteApp;

internal static class BrowserTests
{
    private static void Assert(bool value, string description)
    {
        if (!value) throw new Exception(description);
        Console.WriteLine("PASS: " + description);
    }

    [STAThread]
    private static int Main(string[] args)
    {
        Application.EnableVisualStyles();
        int result = 1;
        var config = new JavaScriptSerializer().Deserialize<AppConfig>(File.ReadAllText(args[0]));
        using (var form = new MainForm(config))
        using (var deadline = new Timer { Interval = 60000 })
        {
            form.ShowInTaskbar = false;
            form.Opacity = 0;
            deadline.Tick += delegate { Console.Error.WriteLine("Browser test timed out"); form.Close(); };
            form.Shown += async delegate
            {
                try
                {
                    Assert(form.FormBorderStyle == FormBorderStyle.None && !form.MinimizeBox && !form.MaximizeBox,
                        "Live browser window has no minimize/maximize buttons");
                    Assert(form.Bounds == Screen.FromControl(form).Bounds, "Live window covers the full monitor");
                    var browser = (WebView2)typeof(MainForm).GetField("browser", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(form);
                    await WaitUntil(() => form.BackColor.ToArgb() == Color.FromArgb(16, 18, 20).ToArgb());
                    Assert(Theme(form).IsDark, "Dark site applies dark Windows theme");
                    foreach (Control control in form.Controls)
                        if (control is ToolStrip) Assert(control.BackColor == form.BackColor, "Toolbar/status follow site background");
                    using (var bitmap = form.Icon.ToBitmap())
                    {
                        Color pixel = bitmap.GetPixel(bitmap.Width / 2, bitmap.Height / 2);
                        Assert(pixel.R == 51 && pixel.G == 204 && pixel.B == 153, "Custom icon loaded from embedded resource");
                    }
                    using (var icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath))
                    using (var bitmap = icon.ToBitmap())
                    {
                        Color pixel = bitmap.GetPixel(bitmap.Width / 2, bitmap.Height / 2);
                        Assert(pixel.G == 204 && pixel.B == 153, "EXE native icon matches uploaded image");
                    }
                    using (var dialog = new ExitDialog(null, Theme(form)))
                        Assert(dialog.BackColor == form.BackColor, "Exit dialog follows dark site");
                    await browser.CoreWebView2.ExecuteScriptAsync("document.body.style.backgroundColor='#f7f8fa'; document.body.style.color='black';");
                    await WaitUntil(() => form.BackColor.ToArgb() == Color.FromArgb(247, 248, 250).ToArgb());
                    Assert(!Theme(form).IsDark, "Theme toggles to light without reload");
                    await browser.CoreWebView2.ExecuteScriptAsync("document.body.innerHTML='<main style=\"position:fixed;inset:0;background:#181a20;color:white\">Dark application root</main>';");
                    await WaitUntil(() => form.BackColor.ToArgb() == Color.FromArgb(24, 26, 32).ToArgb());
                    Assert(Theme(form).IsDark, "Full-page app root overrides white body background");
                    await browser.CoreWebView2.ExecuteScriptAsync("document.body.innerHTML='';document.body.style.backgroundColor='transparent';document.documentElement.style.backgroundColor='transparent';document.documentElement.style.colorScheme='dark';");
                    await WaitUntil(() => form.BackColor.ToArgb() == Color.FromArgb(24, 24, 24).ToArgb());
                    Assert(Theme(form).IsDark, "Transparent dark color scheme detected");
                    browser.Reload();
                    await WaitUntil(() => form.BackColor.ToArgb() == Color.FromArgb(16, 18, 20).ToArgb());
                    Assert(Theme(form).IsDark, "Theme re-detected after navigation");
                    Console.WriteLine("ALL BROWSER CHECKS PASSED");
                    result = 0;
                }
                catch (Exception error) { Console.Error.WriteLine(error); }
                finally { form.Close(); }
            };
            deadline.Start();
            Application.Run(form);
        }
        return result;
    }

    private static AppTheme Theme(MainForm form)
    {
        return (AppTheme)typeof(MainForm).GetField("theme", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(form);
    }

    private static async Task WaitUntil(Func<bool> condition)
    {
        DateTime deadline = DateTime.UtcNow.AddSeconds(15);
        while (!condition())
        {
            if (DateTime.UtcNow > deadline) throw new TimeoutException("Theme did not reach expected state");
            await Task.Delay(100);
        }
    }
}
