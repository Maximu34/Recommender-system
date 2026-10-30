import type { Track } from '../api';

type Props = {
  track: Track;
  label: string;
  playing: boolean;
  onPlay: (t: Track) => void;
  onToggleAlternatives?: () => void;
  alternativesLabel?: string;
};

/**
 * The song the user was looking for, above the recommendations.
 *
 * Answers "did we find your song?" before the list answers "what else sounds
 * like it?". A lyric hit shows the line that matched, so the match explains
 * itself instead of looking arbitrary.
 */
export default function MatchCard({
  track,
  label,
  playing,
  onPlay,
  onToggleAlternatives,
  alternativesLabel,
}: Props) {
  return (
    <div className="match">
      <div className="match-label">{label}</div>
      <div className="match-row">
        {track.artwork_url ? (
          <img className="art" src={track.artwork_url} alt="" />
        ) : (
          <div className="art" />
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="match-title">{track.title}</div>
          <div className="match-artist">{track.artist}</div>
          {track.genre ? (
            <span className="chip" style={{ marginTop: 6, display: 'inline-block' }}>
              {track.genre}
            </span>
          ) : null}
        </div>
        <button
          className={`iconbtn${playing ? ' on' : ''}`}
          style={{ width: 42, height: 42, background: playing ? undefined : '#fff' }}
          aria-label={playing ? 'Pause' : 'Play'}
          onClick={() => onPlay(track)}
        >
          {playing ? '❚❚' : '▶'}
        </button>
      </div>

      {track.matched_line ? (
        <div className="lyric">
          <span>matched this line</span>“{track.matched_line}”
        </div>
      ) : null}

      {onToggleAlternatives ? (
        <button className="linkish" onClick={onToggleAlternatives}>
          {alternativesLabel}
        </button>
      ) : null}
    </div>
  );
}
