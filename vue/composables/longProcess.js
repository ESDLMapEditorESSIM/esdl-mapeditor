import { computed, ref, watchEffect } from "vue";

/**
 * The representation of a long process. Progress can be fetched periodically from a URL.
 */
export class LongProcess {
  constructor(name, url, requestParams, progressField, messageField, failedField, callback) {
    this.name = name;
    this.url = url;
    this.requestParams = requestParams;
    this.progressField = progressField || "progress";
    this.failedField = failedField;
    this.messageField = messageField;
    // If callback is set, call it when the process is completed successfully, containing the final response.
    this.callback = callback;
    this.checkIntervalMs = 10000;
    this.progress = ref(0);
    this.message = ref('');
    this.isFailed = ref(false);
    this.isDone = computed(() => this.progress.value >= 100 || this.isFailed.value)
    this.startTime = null;
  }

  start() {
    this.startTime = new Date();
    this.fetchProgress();
  }

  fetchProgress = () => {
    let target_url = this.url;
    if (this.requestParams) {
      const queryString = new URLSearchParams(self.requestParams).toString();
      target_url += `?${queryString}`;
    }
    fetch(target_url)
      .then(response => response.json())
      .then(data => {
        this.progress.value = data[this.progressField];
        
        if (this.messageField) {
          this.message.value = data[this.messageField];
        }
        if (this.failedField) {
          this.isFailed.value = data[this.failedField];
        }
        if (this.isDone.value && !this.isFailed.value && this.callback) {
          this.callback(data);
        }
        if (!this.isDone.value) {
          setTimeout(this.fetchProgress, this.checkIntervalMs)
        }
      }).catch((error) => {
        console.error("Error while fetching progress", error)
        this.isFailed.value = true;
    });
  }
}

const activeLongProcess = ref(new LongProcess());
const showActiveLongProcess = ref(false);

export function useLongProcessState() {
  const toggleShowActiveLongProcess = () => showActiveLongProcess.value = !showActiveLongProcess.value;

  const startLongProcess = (name, url, requestParams, progress_field, message_field, failed_field, callback) => {
    activeLongProcess.value = new LongProcess(name, url, requestParams, progress_field, message_field, failed_field, callback);
    showActiveLongProcess.value = true;
    activeLongProcess.value.start();

    watchEffect(() => {
      if (activeLongProcess.value.progress >= 100) {
        // TODO: Implement done callback.
      }
    });
  }

  const refreshActiveLongPorcess = () => {
    activeLongProcess.value.fetchProgress();
  }

  return {
    activeLongProcess,
    toggleShowActiveLongProcess,
    showActiveLongProcess,
    startLongProcess,
    refreshActiveLongPorcess,
  }
}
