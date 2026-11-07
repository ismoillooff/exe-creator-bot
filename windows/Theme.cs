using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace WebsiteApp
{
    public sealed class ThemeSnapshot
    {
        public string Background { get; set; }
        public bool IsDark { get; set; }
    }

    internal sealed class AppTheme
    {
        public readonly Color Background;
        public readonly Color Foreground;
        public readonly Color Hover;
        public readonly bool IsDark;

        public AppTheme(Color background, bool dark)
        {
            Background = background;
            IsDark = dark;
            Foreground = dark ? Color.FromArgb(242, 242, 245) : Color.FromArgb(24, 24, 27);
            Hover = ControlPaint.Light(background, dark ? 0.22f : 0.12f);
            if (!dark) Hover = ControlPaint.Dark(background, 0.06f);
        }

        public static AppTheme FromSnapshot(ThemeSnapshot snapshot)
        {
            if (snapshot == null || snapshot.Background == null || snapshot.Background.Length != 7 ||
                snapshot.Background[0] != '#') return null;
            int rgb;
            if (!Int32.TryParse(snapshot.Background.Substring(1), System.Globalization.NumberStyles.HexNumber,
                System.Globalization.CultureInfo.InvariantCulture, out rgb)) return null;
            return new AppTheme(Color.FromArgb((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255), snapshot.IsDark);
        }

        public void Apply(Control control)
        {
            control.BackColor = Background;
            control.ForeColor = Foreground;
            var strip = control as ToolStrip;
            if (strip != null)
            {
                strip.Renderer = new ToolStripProfessionalRenderer(new ThemeColorTable(this));
                foreach (ToolStripItem item in strip.Items)
                {
                    item.BackColor = Background;
                    item.ForeColor = Foreground;
                }
            }
            var button = control as Button;
            if (button != null)
            {
                button.UseVisualStyleBackColor = false;
                button.FlatStyle = FlatStyle.Flat;
                button.FlatAppearance.BorderColor = Hover;
                button.FlatAppearance.MouseOverBackColor = Hover;
            }
            foreach (Control child in control.Controls) Apply(child);
        }

        [DllImport("dwmapi.dll")]
        private static extern int DwmSetWindowAttribute(IntPtr hwnd, int attribute, ref int value, int size);

        public void ApplyTitleBar(Form form)
        {
            if (!form.IsHandleCreated) return;
            try
            {
                int dark = IsDark ? 1 : 0;
                // Eski Windows versiyalarida qo'llab-quvvatlanmagan atributlar e'tiborsiz qoladi.
                DwmSetWindowAttribute(form.Handle, 20, ref dark, 4);
                int caption = ColorTranslator.ToWin32(Background);
                int text = ColorTranslator.ToWin32(Foreground);
                DwmSetWindowAttribute(form.Handle, 35, ref caption, 4);
                DwmSetWindowAttribute(form.Handle, 36, ref text, 4);
            }
            catch (DllNotFoundException) { }
            catch (EntryPointNotFoundException) { }
        }
    }

    internal sealed class ThemeColorTable : ProfessionalColorTable
    {
        private readonly AppTheme theme;
        public ThemeColorTable(AppTheme value) { theme = value; UseSystemColors = false; }
        public override Color ToolStripGradientBegin { get { return theme.Background; } }
        public override Color ToolStripGradientMiddle { get { return theme.Background; } }
        public override Color ToolStripGradientEnd { get { return theme.Background; } }
        public override Color StatusStripGradientBegin { get { return theme.Background; } }
        public override Color StatusStripGradientEnd { get { return theme.Background; } }
        public override Color ToolStripBorder { get { return theme.Background; } }
        public override Color ButtonSelectedBorder { get { return theme.Hover; } }
        public override Color ButtonSelectedGradientBegin { get { return theme.Hover; } }
        public override Color ButtonSelectedGradientMiddle { get { return theme.Hover; } }
        public override Color ButtonSelectedGradientEnd { get { return theme.Hover; } }
        public override Color ButtonPressedGradientBegin { get { return theme.Hover; } }
        public override Color ButtonPressedGradientMiddle { get { return theme.Hover; } }
        public override Color ButtonPressedGradientEnd { get { return theme.Hover; } }
        public override Color SeparatorDark { get { return theme.Hover; } }
        public override Color SeparatorLight { get { return theme.Hover; } }
    }
}
