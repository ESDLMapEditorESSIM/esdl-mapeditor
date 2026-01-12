const PREFIXES = ['Y', 'Z', 'E', 'P', 'T', 'G', 'M', 'k', 'h', 'da', '', 'd', 'c', 'm', 'u', 'n', 'p', 'f', 'a', 'z', 'y'];
const FACTORS = [24, 21, 18, 15, 12, 9, 6, 3, 2, 1, 0, -1, -2, -3, -6, -9, -12, -15, -18, -21, -24];

const WATER_DENSITY = 1000; // kg/m3

const PROPERTIES = {
    energy: {
        baseUnit: "J",
        allowPrefixes: true,
        alternativeUnits: [
            {baseUnit: "Wh", multiplier: 3600}
        ]
    },
    power: {
        baseUnit: "W",
        allowPrefixes: true
    },
    waterFlow: {
        baseUnit: "kg/s",
        allowPrefixes: false,
        alternativeUnits: [
            {baseUnit: "m3/s", multiplier: WATER_DENSITY},
            {baseUnit: "m3/h", multiplier: WATER_DENSITY / 3600}
        ]
    }
};

function buildUnitTable(properties) {
    const table = {};
    for (const [prop, config] of Object.entries(properties)) {
        table[config.baseUnit] = {
            multiplier: 1,
            baseType: prop
        };
        if (config.allowPrefixes) {
            PREFIXES.forEach((p, i) => {
                const unit = p + config.baseUnit;
                table[unit] = {
                    multiplier: 10 ** FACTORS[i],
                    baseType: prop
                };
            });
        }
        if (config.alternativeUnits) {
            config.alternativeUnits.forEach(alt => {
                table[alt.baseUnit] = {
                    multiplier: alt.multiplier,
                    baseType: prop
                };
                if (config.allowPrefixes) {
                    PREFIXES.forEach((p, i) => {
                        const unit = p + alt.baseUnit;
                        table[unit] = {
                            multiplier: alt.multiplier * (10 ** FACTORS[i]),
                            baseType: prop
                        };
                    });
                }
            });
        }
    }
    return table;
}

const unitTable = buildUnitTable(PROPERTIES);

/**
 * Convert a value from a sourceUnit to a targetUnit.
 * See PROPERTIES and PREFIXES for available units.
 *
 * @param {*} value
 * @param {*} sourceUnit
 * @param {*} targetUnit
 */
export const convertUnit = (value, sourceUnit, targetUnit) => {
    const fromUnit = unitTable[sourceUnit];
    const toUnit = unitTable[targetUnit];

    if (!fromUnit) throw new Error(`Unknown unit: ${sourceUnit}`);
    if (!toUnit) throw new Error(`Unknown unit: ${targetUnit}`);

    if (fromUnit.baseType === toUnit.baseType) {
        return value * (fromUnit.multiplier / toUnit.multiplier);
    }

    throw new Error(
        `Cannot convert ${sourceUnit} (${fromUnit.baseType}) to ${targetUnit} (${toUnit.baseType})`
    );
};
