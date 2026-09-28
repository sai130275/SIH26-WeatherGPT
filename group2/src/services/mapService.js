/**
 * Map Service
 * Generates GeoJSON FeatureCollection for Mapbox UI integration in Flutter.
 */

const generateRiskGeoJson = async (centerLat = 17.9689, centerLon = 79.5941) => {
  // Generate risk heat circles / polygons around user region
  const features = [
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [centerLon, centerLat]
      },
      properties: {
        title: "User Location",
        risk_level: "LOW",
        risk_score: 22,
        layer: "user_marker"
      }
    },
    {
      type: "Feature",
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [centerLon - 0.05, centerLat - 0.05],
            [centerLon + 0.05, centerLat - 0.05],
            [centerLon + 0.05, centerLat + 0.05],
            [centerLon - 0.05, centerLat + 0.05],
            [centerLon - 0.05, centerLat - 0.05]
          ]
        ]
      },
      properties: {
        title: "Rain Hazard Zone",
        hazard: "Precipitation",
        risk_level: "MODERATE",
        risk_score: 54,
        fill_color: "#FF9800",
        fill_opacity: 0.35,
        disclaimer: "WeatherGPT prototype risk layer"
      }
    },
    {
      type: "Feature",
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [centerLon + 0.08, centerLat + 0.08],
            [centerLon + 0.15, centerLat + 0.08],
            [centerLon + 0.15, centerLat + 0.15],
            [centerLon + 0.08, centerLat + 0.15],
            [centerLon + 0.08, centerLat + 0.08]
          ]
        ]
      },
      properties: {
        title: "High Wind Hazard Area",
        hazard: "Wind",
        risk_level: "HIGH",
        risk_score: 72,
        fill_color: "#F44336",
        fill_opacity: 0.45,
        disclaimer: "WeatherGPT prototype risk layer"
      }
    }
  ];

  return {
    type: "FeatureCollection",
    features
  };
};

module.exports = {
  generateRiskGeoJson
};
