import type { Track } from '../api';

function clock(s: number): string {
  if (!isFinite(s) || s < 0) return '0:00';
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
}

type Props = {
  track: Track | null;
  playing: boolean;
  position: number;
  duration: number;
  onToggle: () => void;
  onSeek: (fraction: number) => void;
};

export default function NowPlaying({
  track, playing, position, duration, onToggle, onSeek,
}: Props) {
  if (!track) {
    return (
      <div className="player">
        <span className="muted">Nothing playing</span>
      </div>
    );
  }
  const pct = duration > 0 ? (position / duration) * 100 : 0;

  return (
    <div className="player">
      {track.artwork_url ? (
        <img className="art" style={{ width: 46, height: 46 }} src={track.artwork_url} alt="" />
      ) : (
        <div className="art" style={{ width: 46, height: 46 }} />
      )}
      <div style={{ minWidth: 160, maxWidth: 230 }}>
        <div className="row-title">{track.title}</div>
        <div className="row-artist">{track.artist}</div>
      </div>
      <button
        className="iconbtn on"
        style={{ width: 38, height: 38 }}
        aria-label={playing ? 'Pause' : 'Play'}
        onClick={onToggle}
      >
        {playing ? '❚❚' : '▶'}
      </button>
      <span className="time">{clock(position)}</span>
      <div
        className="progress"
        onClick={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          onSeek((e.clientX - r.left) / r.width);
        }}
      >
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      {/* The clip is a 30s preview, and the label says so rather than
          pretending to be a full track. */}
      <span className="time">{clock(duration)} preview</span>
    </div>
  );
}
