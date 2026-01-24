import { useEffect, useState } from "react";

export function useSmoothNumber(target: number, speed = 20) {
  const [value, setValue] = useState(target);

  useEffect(() => {
    const diff = target - value;
    if (diff === 0) return;

    const step = diff / speed;
    const id = setInterval(() => {
      setValue(v => {
        if (Math.abs(target - v) < 1) {
          clearInterval(id);
          return target;
        }
        return v + step;
      });
    }, 16);

    return () => clearInterval(id);
  }, [target]);

  return Math.round(value);
}
