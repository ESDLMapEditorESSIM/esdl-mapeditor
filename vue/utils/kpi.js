const KPI_TERMS = {
    co2: 'CO₂',
    capex: 'CAPEX',
    opex: 'OPEX',
    cop: 'COP',
};

/** Humanize a KPI name for display, optionally followed by a supplied unit. */
export function formatKPIName(name, unit) {
    let label = String(name ?? '').replace(/[_\s]+/g, ' ').trim();
    label = label.replace(/[\p{L}\p{N}]+/gu, term => {
        if (Object.hasOwn(KPI_TERMS, term)) {
            return KPI_TERMS[term];
        }
        return term;
    });
    label = label.charAt(0).toUpperCase() + label.slice(1);
    if (unit && unit.trim()) {
        label += ' [' + unit.trim() + ']';
    }
    return label;
}
