import { useEffect, useState } from "react";
import { getPrediction } from "../services/api";

export default function PredictionsPanel({ zones }: { zones: any[] }) {
  const [predictions, setPredictions] = useState<Record<number, any>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPredictions = async () => {
      setLoading(true);
      const preds: Record<number, any> = {};
      
      for (const zone of zones) {
        const pred = await getPrediction(zone.id);
        if (pred) {
          preds[zone.id] = pred;
        }
      }
      
      setPredictions(preds);
      setLoading(false);
    };

    if (zones.length > 0) {
      loadPredictions();
    }
  }, [zones]);

  return (
    <div className="rounded-xl border border-blue-500/40 bg-blue-500/10 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-blue-400">🔮 LSTM Predictions</h3>
        {loading && <span className="text-xs text-blue-300 animate-pulse">Loading...</span>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {zones.map((zone) => {
          const pred = predictions[zone.id];
          const riskColor =
            !pred ? "text-gray-400" :
            pred.predicted_level === "Severe"
              ? "text-red-400"
              : pred.predicted_level === "Elevated"
              ? "text-orange-400"
              : pred.predicted_level === "Caution"
              ? "text-yellow-400"
              : "text-green-400";

          return (
            <div
              key={zone.id}
              className="rounded-lg border border-slate-700/50 bg-slate-900/50 p-4"
            >
              <p className="text-sm font-semibold text-slate-300 truncate">
                {zone.name}
              </p>
              {pred ? (
                <>
                  <div className="mt-2">
                    <p className={`text-lg font-bold ${riskColor}`}>
                      {pred.predicted_risk_score}
                    </p>
                    <p className={`text-xs ${riskColor}`}>
                      {pred.predicted_level}
                    </p>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    Next Period Prediction
                  </p>
                </>
              ) : (
                <p className="text-xs text-slate-500 mt-2">Training model...</p>
              )}
            </div>
          );
        })}
      </div>

      <p className="text-xs text-blue-300 mt-4">
        💡 LSTM predicts the next risk score based on historical patterns. Green = Safe, Yellow = Caution, Orange = Elevated, Red = Severe
      </p>
    </div>
  );
}
