// Paleta de cores para props de SVG do recharts (stroke/fill/contentStyle),
// que não aceitam classes Tailwind — precisam do hex resolvido em JS conforme
// o tema ativo. Use com `const { mode } = useTheme(); const cc = chartColors(mode === 'dark');`
export function chartColors(isDark: boolean) {
    return {
        axis: isDark ? '#94a3b8' : '#64748b',
        grid: isDark ? '#334155' : '#e2e8f0',
        tooltipBg: isDark ? '#1e293b' : '#ffffff',
        tooltipBorder: isDark ? '#334155' : '#e2e8f0',
        tooltipText: isDark ? '#f1f5f9' : '#111827',
        tooltipItemText: isDark ? '#f8fafc' : '#111827',
        tooltipLabelText: isDark ? '#94a3b8' : '#6b7280',
        legendText: isDark ? '#cbd5e1' : '#475569',
        neutralBar: isDark ? '#334155' : '#cbd5e1',
    };
}
