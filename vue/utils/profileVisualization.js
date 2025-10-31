const config = {
  profileMaxDataPoints: 100,
  dateTimeFormat: "YYYY-MM-DD HH:mm:ss",
};

const normalizePlotlyDateTimeStr = (dtStr) => {
  // Check if it's only a date (no time part at all)
  if (!dtStr.includes(" ")) {
    return `${dtStr} 00:00:00`;
  }

  // Split into date and time parts
  const [datePart, timePartRaw] = dtStr.split(" ");
  const timePart = timePartRaw.split(".")[0]; // remove milliseconds if any

  // Normalize time parts to full HH:mm:ss
  const parts = timePart.split(":");
  const [hh = "00", mm = "00", ss = "00"] = parts;

  return `${datePart} ${hh.padStart(2, "0")}:${mm.padStart(2, "0")}:${ss.padStart(2, "0")}`;
};

export { config, normalizePlotlyDateTimeStr };
