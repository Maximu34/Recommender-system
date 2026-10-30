import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { radius, space, theme } from '../theme';

/**
 * Sparkline of the pitch contour pYIN extracted from the hum.
 *
 * Worth showing: it makes the melody-matching step visible instead of a black
 * box, and it tells the user straight away whether the microphone actually
 * heard a tune or just noise.
 *
 * Drawn with plain Views so the app needs no SVG dependency.
 */
export default function Contour({ points }: { points: number[] }) {
  if (!points.length) return null;

  // Downsample to a fixed number of bars so long hums stay readable.
  const BARS = 48;
  const step = Math.max(1, Math.floor(points.length / BARS));
  const sampled: number[] = [];
  for (let i = 0; i < points.length; i += step) sampled.push(points[i]);

  const min = Math.min(...sampled);
  const max = Math.max(...sampled);
  const span = max - min || 1;

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>your tune</Text>
      <View style={styles.chart}>
        {sampled.map((v, i) => (
          <View
            key={i}
            style={[
              styles.bar,
              { height: 4 + ((v - min) / span) * 44 },
            ]}
          />
        ))}
      </View>
      <Text style={styles.range}>{(max - min).toFixed(1)} semitone range</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    marginTop: space(2),
    width: '100%',
    backgroundColor: theme.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: theme.border,
    padding: space(1.25),
  },
  label: { color: theme.textDim, fontSize: 11, marginBottom: space(0.75) },
  chart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 52,
    gap: 2,
  },
  bar: {
    flex: 1,
    backgroundColor: theme.accent,
    borderRadius: 1.5,
    minWidth: 2,
  },
  range: { color: theme.textDim, fontSize: 10.5, marginTop: space(0.75) },
});
