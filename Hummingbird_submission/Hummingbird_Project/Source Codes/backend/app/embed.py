"""CLAP embeddings.

CLAP maps audio *and* text into one shared 512-d space, which is why the same
model serves two features: "songs that sound like this one" (audio query) and
"dreamy guitar for a rainy evening" (text query).

Note what this module is *not* used for: looking up a song by its title. That
is a metadata lookup in :mod:`app.store`. Routing title search through a text
encoder returns semantically-plausible wrong songs instead of the song the
user actually typed.
"""

from __future__ import annotations

import numpy as np

from . import config

_model = None
_processor = None


def _load():
    """Load CLAP once, on first use."""
    global _model, _processor
    if _model is None:
        import torch
        from transformers import ClapModel, ClapProcessor

        _model = ClapModel.from_pretrained(config.CLAP_MODEL)
        _model.eval()
        torch.set_num_threads(max(1, (torch.get_num_threads() or 4)))
        _processor = ClapProcessor.from_pretrained(config.CLAP_MODEL)
    return _model, _processor


def _audio_kwarg(processor) -> str:
    """Name of the processor's audio parameter: 'audio' (v5) or 'audios' (v4).

    This must be detected, not guessed with try/except: ``ClapProcessor.__call__``
    ends in ``**kwargs``, so passing the wrong name raises nothing -- the
    waveforms are silently dropped and the model embeds nothing.
    """
    import inspect

    params = inspect.signature(processor.__call__).parameters
    if "audio" in params:
        return "audio"
    if "audios" in params:
        return "audios"
    raise RuntimeError(
        "ClapProcessor exposes neither 'audio' nor 'audios'; "
        "check the installed transformers version"
    )


def _process_audio(processor, waveforms: list[np.ndarray]):
    import torch

    kwargs = {
        _audio_kwarg(processor): waveforms,
        "sampling_rate": config.CLAP_SR,
        "return_tensors": "pt",
        "padding": True,
    }
    inputs = processor(**kwargs)

    # The feature extractor flags anything longer than the model's 10s window
    # as `is_longer`, which routes the audio through CLAP's feature-fusion
    # branch. This checkpoint has enable_fusion=False, so those weights were
    # never trained and the resulting embeddings collapse towards each other
    # (measured: mean pairwise cosine 0.92 with the flag on, 0.73 with it off).
    if "is_longer" in inputs:
        inputs["is_longer"] = torch.zeros_like(inputs["is_longer"])
    return inputs


def _windows(y: np.ndarray) -> list[np.ndarray]:
    """Split a clip into consecutive fixed windows of the model's input length.

    CLAP's feature extractor defaults to ``truncation="rand_trunc"``: it keeps
    a *random* 10s crop, so embedding the same track twice gives two different
    vectors. That is unusable for an index. Taking fixed consecutive windows
    and mean-pooling them is deterministic and uses the whole clip.
    """
    win = config.CLAP_WINDOW_S * config.CLAP_SR
    if len(y) <= win:
        return [y]
    # Only whole windows. A short trailing fragment would be zero-padded to
    # the model's input length, and that padded window drags the mean-pooled
    # embedding around -- clips differing by a second would land in different
    # places for no musical reason.
    return [y[i:i + win] for i in range(0, len(y) - win + 1, win)]


def _features_to_numpy(out) -> np.ndarray:
    """Pull the (n, 512) embedding out of whatever the model returned.

    transformers 4 returned a bare tensor from ``get_audio_features``;
    transformers 5 returns a ``BaseModelOutputWithPooling`` whose
    ``pooler_output`` holds the projected embedding (``last_hidden_state`` is
    a much larger pre-projection tensor and is *not* interchangeable).
    """
    tensor = getattr(out, "pooler_output", None)
    if tensor is None:
        tensor = out  # transformers 4 style: already a tensor
    if not hasattr(tensor, "cpu"):
        raise TypeError(
            f"unexpected CLAP output {type(out).__name__}; cannot find embedding tensor"
        )
    return tensor.cpu().numpy()


def _l2(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (x / norms).astype(np.float32)


def embed_audio(waveforms: list[np.ndarray]) -> np.ndarray:
    """Embed mono waveforms sampled at ``config.CLAP_SR``. Returns (n, 512).

    Each clip is split into fixed windows, embedded, and mean-pooled, so the
    result is deterministic and covers the whole clip rather than one random
    10-second crop.
    """
    import torch

    model, processor = _load()

    # Flatten all windows into one batch, remembering which clip each came from.
    flat: list[np.ndarray] = []
    owner: list[int] = []
    for i, y in enumerate(waveforms):
        for w in _windows(y):
            flat.append(w)
            owner.append(i)

    inputs = _process_audio(processor, flat)
    with torch.no_grad():
        out = model.get_audio_features(**inputs)
    vecs = _l2(_features_to_numpy(out))

    owner_arr = np.asarray(owner)
    pooled = np.stack([vecs[owner_arr == i].mean(axis=0)
                       for i in range(len(waveforms))])
    return _l2(pooled)


def embed_text(texts: list[str]) -> np.ndarray:
    """Embed free-text mood/vibe descriptions. Returns (n, 512)."""
    import torch

    model, processor = _load()
    inputs = processor(text=texts, return_tensors="pt", padding=True)
    with torch.no_grad():
        out = model.get_text_features(**inputs)
    return _l2(_features_to_numpy(out))


def embedding_dim() -> int:
    model, _ = _load()
    return int(model.config.projection_dim)
