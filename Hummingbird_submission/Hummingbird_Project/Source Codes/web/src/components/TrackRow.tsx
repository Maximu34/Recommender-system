import type { Descriptors, Track } from '../api';

/** Plain-language reasons this track resembles the seed. */
function explain(a?: Descriptors | null, b?: Descriptors | null): string[] {
  if (!a || !b) return [];
  const out: string[] = [];
  const dTempo = Math.abs(a.tempo_bpm - b.tempo_bpm);
  if (dTempo < 6) out.push(`same tempo (~${Math.round(b.tempo_bpm)} BPM)`);
  else if (dTempo < 15) out.push(`similar tempo (${Math.round(b.tempo_bpm)} BPM)`);

  if (a.key === b.key) out.push(`same key (${b.key})`);
  else if (a.key.split(' ')[1] === b.key.split(' ')[1])
    out.push(`both ${b.key.split(' ')[1]}`);

  const ratio = b.brightness_hz / (a.brightness_hz || 1);
  if (ratio > 0.85 && ratio < 1.18) out.push('similar brightness');
  else out.push(ratio >= 1.18 ? 'brighter' : 'darker');

  return out.slice(0, 3);
}

type Props = {
  track: Track;
  seed?: Descriptors | null;
  playing: boolean;
  onPlay: (t: Track) => void;
  onSelect?: (t: Track) => void;
};

export default function TrackRow({ track, seed, playing, onPlay, onSelect }: Props) {
  const score = track.similarity ?? track.score;
  const reasons = explain(seed, track.descriptors);

  return (
    <div>
      <div
        className="row"
        onClick={() => onSelect?.(track)}
        style={{ cursor: onSelect ? 'pointer' : 'default' }}
      >
        {track.artwork_url ? (
          <img className="art" src={track.artwork_url} alt="" />
        ) : (
          <div className="art" />
        )}
        <div className="row-meta">
          <div className="row-title">{track.title}</div>
          <div className="row-artist">{track.artist}</div>
        </div>
        {track.genre ? <span className="chip">{track.genre}</span> : null}
        {score !== undefined ? (
          <span className="score">{score.toFixed(2)}</span>
        ) : null}
        <button
          className={`iconbtn${playing ? ' on' : ''}`}
          aria-label={playing ? 'Pause' : 'Play'}
          onClick={(e) => {
            e.stopPropagation();
            onPlay(track);
          }}
        >
          {playing ? '❚❚' : '▶'}
        </button>
      </div>
      {reasons.length ? <div className="why">{reasons.join(' · ')}</div> : null}
    </div>
  );
}
