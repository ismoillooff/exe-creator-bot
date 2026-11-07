// Faqat sahifa ranglarini o'qiydi; DOM va sayt sozlamalarini o'zgartirmaydi.
(() => {
    if (!document.documentElement || !document.body) return null;
    const rootStyle = getComputedStyle(document.documentElement);
    const bodyStyle = getComputedStyle(document.body);
    const darkPreference = rootStyle.colorScheme === 'dark' || bodyStyle.colorScheme === 'dark' ||
        (rootStyle.colorScheme.includes('dark') && matchMedia('(prefers-color-scheme: dark)').matches);
    const base = darkPreference ? [24, 24, 24] : [255, 255, 255];
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return null;
    const cache = new Map();
    function rgba(element) {
        if (cache.has(element)) return cache.get(element);
        const color = getComputedStyle(element).backgroundColor;
        ctx.clearRect(0, 0, 1, 1);
        ctx.fillStyle = color;
        ctx.fillRect(0, 0, 1, 1);
        const pixel = Array.from(ctx.getImageData(0, 0, 1, 1).data);
        cache.set(element, pixel);
        return pixel;
    }
    function composite(background, foreground) {
        const alpha = foreground[3] / 255;
        return background.map((value, i) => value * (1 - alpha) + foreground[i] * alpha);
    }
    const points = [[.12, .12], [.5, .12], [.88, .12], [.12, .5], [.5, .5], [.88, .5], [.5, .88]];
    const colors = points.map(([x, y]) => {
        let result = composite(composite(base, rgba(document.documentElement)), rgba(document.body));
        const stack = document.elementsFromPoint(Math.max(0, innerWidth * x), Math.max(0, innerHeight * y));
        for (const element of stack.slice(0, 40).reverse()) {
            if (element !== document.documentElement && element !== document.body)
                result = composite(result, rgba(element));
        }
        return result.map(Math.round);
    });
    const brightness = rgb => .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
    colors.sort((a, b) => brightness(a) - brightness(b));
    const selected = colors[Math.floor(colors.length / 2)];
    return { Background: '#' + selected.map(n => n.toString(16).padStart(2, '0')).join(''),
             IsDark: brightness(selected) < 145 };
})();
