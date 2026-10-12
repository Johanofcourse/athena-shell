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
  "anaheim-ca": [18.082, 60.389],
  "atlanta-ga": [71.74, 64.19],
  "austin-tx": [50.906, 78.557],
  "baltimore-md": [81.922, 41.614],
  "boston-ma": [89.464, 27.143],
  "charlotte-nc": [76.935, 57.069],
  "chicago-il": [66.133, 37.817],
  "cincinnati-oh": [69.921, 43.372],
  "cleveland-oh": [74.286, 31.291],
  "columbus-oh": [72.262, 38.53],
  "dallas-tx": [52.093, 69.473],
  "denver-co": [40.355, 44.744],
  "detroit-mi": [72.426, 28.571],
  "fort-lauderdale-fl": [80.767, 89.939],
  "fort-worth-tx": [49.897, 70.218],
  "houston-tx": [57.388, 79.918],
  "indianapolis-in": [67.544, 42.179],
  "jacksonville-fl": [77.26, 75.744],
  "kansas-city-mo": [53.622, 46.208],
  "las-vegas-nv": [24.592, 54.367],
  "los-angeles-ca": [17.237, 59.453],
  "miami-fl": [80.056, 90.093],
  "milwaukee-wi": [67.129, 34.071],
  "minneapolis-mn": [56.944, 25.901],
  "montgomery-county-pa": [83.537, 38.925],
  "nashville-tn": [67.843, 58.892],
  "nassau-county-ny": [86.191, 37.2],
  "new-brunswick-nj": [84.896, 37.91],
  "new-york-ny": [85.857, 37.057],
  "newark-nj": [85.247, 37.033],
  "oakland-ca": [12.303, 45.055],
  "orlando-fl": [78.358, 82.113],
  "philadelphia-pa": [83.68, 39.837],
  "phoenix-az": [27.346, 65.654],
  "pittsburgh-pa": [76.508, 35.905],
  "portland-or": [18.041, 18.352],
  "providence-ri": [89.801, 31.825],
  "riverside-ca": [22.18, 59.007],
  "sacramento-ca": [16.989, 41.131],
  "san-antonio-tx": [47.664, 81.697],
  "san-diego-ca": [18.961, 63.358],
  "san-francisco-ca": [12.172, 44.995],
  "san-jose-ca": [13.086, 49.223],
  "seattle-wa": [21.358, 13.03],
  "st-louis-mo": [62.128, 52.969],
  "tampa-fl": [76.014, 83.387],
  "virginia-beach-va": [83.374, 51.225],
  "warren-mi": [72.519, 29.142],
  "washington-dc": [80.608, 43.099],
  "west-palm-beach-fl": [80.872, 87.86],
};
