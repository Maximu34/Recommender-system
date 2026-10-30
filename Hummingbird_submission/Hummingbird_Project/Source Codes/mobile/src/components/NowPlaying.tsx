import React from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

import type { Track } from '../api';
import { radius, space, theme } from '../theme';

type Props = {
  track: Track;
  playing: boolean;
  buffering: boolean;
  position: number;
  duration: number;
  onToggle: () => void;
  onClose: () => void;
};

function clock(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

/**
 * Persistent playback bar.
 *
 * What plays is the cached 30-second preview clip -- that is what the catalog
 * legally holds, so the bar shows the clip's own elapsed/remaining time rather
 * than pretending to be a full-length player.
 */
export default function NowPlaying({
  track,
  playing,
  buffering,
  position,
  duration,
  onToggle,
  onClose,
}: Props) {
  const pct = duration > 0 ? Math.min(100, (position / duration) * 100) : 0;

  return (
    <View style={styles.wrap}>
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${pct}%` }]} />
      </View>

      <View style={styles.row}>
        {track.artwork_url ? (
          <Image source={{ uri: track.artwork_url }} style={styles.art} />
        ) : (
          <View style={[styles.art, styles.artFallback]} />
        )}

        <View style={styles.meta}>
          <Text style={styles.title} numberOfLines={1}>
            {track.title}
          </Text>
          <Text style={styles.artist} numberOfLines={1}>
            {track.artist} · {clock(position)} / {clock(duration)} preview
          </Text>
        </View>

        <Pressable hitSlop={10} style={styles.btn} onPress={onToggle}>
          <Text style={styles.btnIcon}>
            {buffering ? '…' : playing ? '❚❚' : '▶'}
          </Text>
        </Pressable>
        <Pressable hitSlop={10} style={styles.close} onPress={onClose}>
          <Text style={styles.closeIcon}>✕</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: theme.surfaceAlt,
    borderTopWidth: 1,
    borderColor: theme.border,
    borderTopLeftRadius: radius.md,
    borderTopRightRadius: radius.md,
    overflow: 'hidden',
  },
  progressTrack: { height: 3, backgroundColor: theme.border },
  progressFill: { height: 3, backgroundColor: theme.accent },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: space(1.5),
    paddingVertical: space(1.25),
  },
  art: { width: 40, height: 40, borderRadius: radius.sm, marginRight: space(1.25) },
  artFallback: { backgroundColor: theme.accentSoft },
  meta: { flex: 1, minWidth: 0 },
  title: { color: theme.text, fontSize: 14, fontWeight: '600' },
  artist: { color: theme.textDim, fontSize: 11.5, marginTop: 2 },
  btn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: theme.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnIcon: { color: '#fff', fontSize: 13 },
  close: { paddingLeft: space(1.25), paddingRight: 2 },
  closeIcon: { color: theme.textDim, fontSize: 15 },
});
