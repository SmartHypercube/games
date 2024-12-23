import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.mjs';
import { zzfx } from 'https://cdn.jsdelivr.net/npm/zzfx@1.3.0/ZzFX.js';

async function loadSpritesheet(palette32, url) {
  const image = new Image();
  image.src = url;
  await new Promise(resolve => {
    image.onload = resolve;
  });
  const canvas = document.createElement('canvas');
  canvas.width = image.width;
  canvas.height = image.height;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(image, 0, 0);
  const imageData8 = ctx.getImageData(0, 0, image.width, image.height);
  const imageData32 = new Uint32Array(imageData8.data.buffer);
  const data = new Uint8Array(imageData32.length);
  for (let i = 0; i < imageData32.length; i++) {
    data[i] = palette32.indexOf(imageData32[i]);
  }
  return { width: image.width, height: image.height, data };
}

async function main() {
  const pyodide = await loadPyodide();
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  const imageData8 = ctx.createImageData(canvas.width, canvas.height);
  const imageData32 = new Uint32Array(imageData8.data.buffer);
  let interacted = false;

  function resize() {
    const scale = devicePixelRatio * visualViewport.scale;
    const width = canvas.parentNode.clientWidth * scale;
    const height = canvas.parentNode.clientHeight * scale;
    const multiplier = Math.floor(Math.max(1, Math.min(width / canvas.width, height / canvas.height)));
    canvas.style.width = `${canvas.width * multiplier / scale}px`;
    canvas.style.height = `${canvas.height * multiplier / scale}px`;
  }

  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(canvas.parentNode, { box: 'content-box' });
  visualViewport.addEventListener('resize', resize);

  const palette8 = new Uint8Array([
    0x1a, 0x1c, 0x2c, 0xff,
    0x5d, 0x27, 0x5d, 0xff,
    0xb1, 0x3e, 0x53, 0xff,
    0xef, 0x7d, 0x57, 0xff,
    0xff, 0xcd, 0x75, 0xff,
    0xa7, 0xf0, 0x70, 0xff,
    0x38, 0xb7, 0x64, 0xff,
    0x25, 0x71, 0x79, 0xff,
    0x29, 0x36, 0x6f, 0xff,
    0x3b, 0x5d, 0xc9, 0xff,
    0x41, 0xa6, 0xf6, 0xff,
    0x73, 0xef, 0xf7, 0xff,
    0xf4, 0xf4, 0xf4, 0xff,
    0x94, 0xb0, 0xc2, 0xff,
    0x56, 0x6c, 0x86, 0xff,
    0x33, 0x3c, 0x57, 0xff,
  ]);
  const palette32 = new Uint32Array(palette8.buffer);
  const screen = new Uint8Array(canvas.width * canvas.height);
  const spritesheet = await loadSpritesheet(palette32, 'spritesheet.png');
  const paletteMap = new Uint8Array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]);
  let borderColor = 0;

  pyodide.registerJsModule('c', {
    clear_screen: c => {
      screen.fill(c);
      borderColor = c;
    },
    set_pixel: (x, y, c) => {
      if (x >= 0 && x < canvas.width && y >= 0 && y < canvas.height) {
        screen[y * canvas.width + x] = c;
      }
    },
    get_pixel: (x, y) => {
      if (x >= 0 && x < canvas.width && y >= 0 && y < canvas.height) {
        return screen[y * canvas.width + x];
      } else {
        return 0;
      }
    },
    fill_rect: (x, y, w, h, c) => {
      for (let i = 0; i < h; i++) {
        if (y + i >= 0 && y + i < canvas.height) {
          for (let j = 0; j < w; j++) {
            if (x + j >= 0 && x + j < canvas.width) {
              screen[(y + i) * canvas.width + x + j] = c;
            }
          }
        }
      }
    },
    set_palette_map: (l) => {
      for (let i = 0; i < paletteMap.length; i++) {
        paletteMap[i] = i < l.length ? l[i] : 255;
      }
    },
    draw_sprite: (dx, dy, sx, sy, w, h) => {
      for (let i = 0; i < h; i++) {
        if (dy + i >= 0 && dy + i < canvas.height) {
          for (let j = 0; j < w; j++) {
            if (dx + j >= 0 && dx + j < canvas.width) {
              const c = paletteMap[spritesheet.data[(sy + i) * spritesheet.width + sx + j]];
              if (c !== 255) {
                screen[(dy + i) * canvas.width + dx + j] = c;
              }
            }
          }
        }
      }
    },
    sfx: (l) => {
      if (interacted) {
        zzfx(...l);
      }
    },
    load_high_score: (s) => {
      return JSON.parse(localStorage.getItem(`high_score_${s}`));
    },
    save_high_score: (s, v) => {
      localStorage.setItem(`high_score_${s}`, JSON.stringify(v));
    },
    pause: () => {
      pause(true);
    },
  });

  await pyodide.runPythonAsync(`
    from pyodide.http import pyfetch
    response = await pyfetch('game.py')
    with open('game.py', 'wb') as f:
      f.write(await response.bytes())
  `);
  const game = pyodide.pyimport('game');

  let buttons = [false];
  function updateButton(id, pressed) {
    if (buttons[id] !== pressed) {
      buttons[id] = pressed;
      game.event('button', id, pressed);
    }
  }
  window.addEventListener('keydown', e => {
    if (e.key === ' ') {
      e.preventDefault();
      updateButton(0, true);
      if (pausedBefore) {
        pause(false);
      }
      interacted = true;
    }
  });
  window.addEventListener('keyup', e => {
    if (e.key === ' ') {
      e.preventDefault();
      updateButton(0, false);
    }
  });
  window.addEventListener('pointerdown', e => {
    if (e.button === 0) {
      e.preventDefault();
      updateButton(0, true);
      if (e.target === canvas) {
        const rect = canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) * canvas.width / rect.width);
        const y = Math.floor((e.clientY - rect.top) * canvas.height / rect.height);
        game.event('pointerdown', 0, [x, y]);
      }
      if (pausedBefore) {
        pause(false);
      }
      interacted = true;
    }
  });
  window.addEventListener('pointerup', e => {
    if (e.button === 0) {
      e.preventDefault();
      updateButton(0, false);
    }
  });
  window.addEventListener('touchstart', e => {
    e.preventDefault();
    updateButton(0, true);
    if (e.target === canvas) {
      const rect = canvas.getBoundingClientRect();
      const x = Math.floor((e.touches[0].clientX - rect.left) * canvas.width / rect.width);
      const y = Math.floor((e.touches[0].clientY - rect.top) * canvas.height / rect.height);
      game.event('pointerdown', 0, [x, y]);
    }
    if (pausedBefore) {
      pause(false);
    }
    interacted = true;
  });
  window.addEventListener('touchend', e => {
    e.preventDefault();
    updateButton(0, false);
  });

  let paused = false;
  let pausedBefore = false;
  function pause(state) {
    return;
    if (paused !== state) {
      paused = state;
      game.event('pause', 0, state);
    }
  }
  window.addEventListener('blur', e => {
    pause(true);
  });
  window.addEventListener('keydown', e => {
    if (e.key === 'Escape' || e.key === 'p') {
      e.preventDefault();
      pause(!paused);
    }
  });

  let tickTime = 0;
  function tick() {
    if (!paused) {
      game.tick();
    }
    pausedBefore = paused;
    for (let i = 0; i < screen.length; i++) {
      imageData32[i] = palette32[screen[i]];
    }
    ctx.putImageData(imageData8, 0, 0);
    document.body.style.backgroundColor = `rgb(${palette8[borderColor * 4]}, ${palette8[borderColor * 4 + 1]}, ${palette8[borderColor * 4 + 2]})`;
    const time = performance.now();
    document.getElementById('debug').textContent = 'Tick time: ' + Array(Math.min(1000, Math.max(0, Math.round(time - tickTime)))).fill('#').join('');
    tickTime = Math.max(tickTime + 1000 / 60, time);
    setTimeout(tick, tickTime - time);
  }
  tick();
}

document.addEventListener('DOMContentLoaded', main);
