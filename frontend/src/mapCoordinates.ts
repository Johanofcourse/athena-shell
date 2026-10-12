/** Pixel position of each metro on colton-us-map-1870s.jpg, as a percent
 * of the image's own width/height - [xPct, yPct]. Not derived from a
 * map projection (the source is a scanned 1870s Colton atlas engraving,
 * not a geodetic dataset) - calibrated by hand against ~39 reference
 * points read directly off the scan (labeled cities, cross-checked
 * against a handful of the map's own printed longitude/latitude ticks),
 * fit with a thin-plate spline (exact at every reference point, smoothly
 * interpolated between them - the standard technique for georeferencing
 * a non-uniformly-distorted historical map scan), then applied to every
 * real metro coordinate in market_crosswalk.py's METRO_COORDINATES.
 * Verified by rendering all 50 pins back onto the source scan and
 * checking they land in geographically sane positions (see
 * UsMetroMap.tsx's map image for the result) - this is a decorative,
 * antique-styled background, not a claim of survey-grade accuracy, so
 * "looks right over the real scan" was the bar, not sub-pixel precision. */
export const METRO_MAP_COORDINATES: Record<string, [number, number]> = {
  "anaheim-ca": [11.744, 59.311],
  "atlanta-ga": [69.207, 63.131],
  "austin-tx": [46.897, 77.574],
  "baltimore-md": [80.112, 40.438],
  "boston-ma": [88.188, 25.891],
  "charlotte-nc": [74.771, 55.974],
  "chicago-il": [63.202, 36.62],
  "cincinnati-oh": [67.26, 42.205],
  "cleveland-oh": [71.934, 30.06],
  "columbus-oh": [69.766, 37.337],
  "dallas-tx": [48.167, 68.442],
  "denver-co": [35.597, 43.584],
  "detroit-mi": [69.942, 27.327],
  "fort-lauderdale-fl": [78.875, 89.015],
  "fort-worth-tx": [45.815, 69.191],
  "houston-tx": [53.837, 78.942],
  "indianapolis-in": [64.714, 41.006],
  "jacksonville-fl": [75.119, 74.746],
  "kansas-city-mo": [49.804, 45.056],
  "las-vegas-nv": [18.716, 53.257],
  "los-angeles-ca": [10.84, 58.37],
  "miami-fl": [78.113, 89.171],
  "milwaukee-wi": [64.27, 32.856],
  "minneapolis-mn": [53.362, 24.643],
  "montgomery-county-pa": [81.841, 37.735],
  "nashville-tn": [65.034, 57.806],
  "nassau-county-ny": [84.682, 36.0],
  "new-brunswick-nj": [83.296, 36.715],
  "new-york-ny": [84.325, 35.857],
  "newark-nj": [83.672, 35.833],
  "oakland-ca": [5.556, 43.897],
  "orlando-fl": [76.294, 81.148],
  "philadelphia-pa": [81.994, 38.652],
  "phoenix-az": [21.666, 64.603],
  "pittsburgh-pa": [74.313, 34.699],
  "portland-or": [11.701, 17.054],
  "providence-ri": [88.549, 30.598],
  "riverside-ca": [16.134, 57.921],
  "sacramento-ca": [10.575, 39.952],
  "san-antonio-tx": [43.425, 80.73],
  "san-diego-ca": [12.686, 62.295],
  "san-francisco-ca": [5.416, 43.836],
  "san-jose-ca": [6.394, 48.087],
  "seattle-wa": [15.253, 11.705],
  "st-louis-mo": [58.914, 51.852],
  "tampa-fl": [73.784, 82.429],
  "virginia-beach-va": [81.666, 50.099],
  "warren-mi": [70.042, 27.901],
  "washington-dc": [78.704, 41.93],
  "west-palm-beach-fl": [78.987, 86.925],
};
