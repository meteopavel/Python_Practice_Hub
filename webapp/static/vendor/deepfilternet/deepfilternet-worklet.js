// AudioWorkletProcessor для DeepFilterNet3 (WASM, wasm-bindgen "web" target).
// Модель зашита в deepfilternet3.wasm на этапе сборки (df_create_default) —
// отдельно тянуть файл модели не нужно, только сам .wasm.
import { initSync, df_create_default, df_get_frame_length, df_set_atten_lim, df_set_post_filter_beta, df_process_frame } from '/static/vendor/deepfilternet/deepfilternet3.js';

const ATTEN_LIM_DB_DEFAULT = 100;
const POST_FILTER_BETA_DEFAULT = 0.02;

class DeepFilterNetProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const { wasmBinary, attenLimDb, postFilterBeta } = options.processorOptions;
    this.ready = false;
    this.bypass = false;
    try {
      initSync(wasmBinary);
      this.state = df_create_default(attenLimDb ?? ATTEN_LIM_DB_DEFAULT);
      df_set_post_filter_beta(this.state, postFilterBeta ?? POST_FILTER_BETA_DEFAULT);
      this.frameLength = df_get_frame_length(this.state);
      // Кольцевой буфер на случай, что frameLength (DFN — 480 сэмплов = 10мс
      // на 48kHz) не совпадает с рендер-квантом AudioWorklet (всегда 128).
      this.ringSize = this.frameLength * 4;
      this.inBuf = new Float32Array(this.ringSize);
      this.outBuf = new Float32Array(this.ringSize);
      this.inWrite = 0;
      this.inRead = 0;
      this.outWrite = 0;
      this.outRead = 0;
      this.frame = new Float32Array(this.frameLength);
      this.ready = true;
    } catch (e) {
      console.error('DeepFilterNet init failed in worklet:', e);
      this.ready = false;
    }
    this.port.onmessage = (event) => {
      const { type, value } = event.data || {};
      if (type === 'set_bypass') this.bypass = Boolean(value);
      else if (type === 'set_atten_lim' && this.ready) df_set_atten_lim(this.state, value);
      else if (type === 'destroy' && this.ready) { this.state = null; this.ready = false; }
    };
  }

  available(writePos, readPos) {
    return (writePos - readPos + this.ringSize) % this.ringSize;
  }

  process(inputs, outputs) {
    const input = inputs[0] && inputs[0][0];
    const output = outputs[0] && outputs[0][0];
    if (!input || !output) return true;

    if (!this.ready || this.bypass) {
      output.set(input);
      return true;
    }

    for (let i = 0; i < input.length; i++) {
      this.inBuf[this.inWrite] = input[i];
      this.inWrite = (this.inWrite + 1) % this.ringSize;
    }

    while (this.available(this.inWrite, this.inRead) >= this.frameLength) {
      for (let i = 0; i < this.frameLength; i++) {
        this.frame[i] = this.inBuf[this.inRead];
        this.inRead = (this.inRead + 1) % this.ringSize;
      }
      const processed = df_process_frame(this.state, this.frame);
      for (let i = 0; i < processed.length; i++) {
        this.outBuf[this.outWrite] = processed[i];
        this.outWrite = (this.outWrite + 1) % this.ringSize;
      }
    }

    if (this.available(this.outWrite, this.outRead) >= output.length) {
      for (let i = 0; i < output.length; i++) {
        output[i] = this.outBuf[this.outRead];
        this.outRead = (this.outRead + 1) % this.ringSize;
      }
    } else {
      output.set(input);
    }
    return true;
  }
}

registerProcessor('deepfilternet-processor', DeepFilterNetProcessor);
