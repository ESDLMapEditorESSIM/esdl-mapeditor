import { computed, ref, watchEffect } from "vue";

/**
 * The representation of a long process. Progress can be fetched periodically from a URL.
 */
export class LongProcess {
  constructor(name, url, progressField, messageField) {
    this.name = name;
    this.url = url;
    this.progressField = progressField;
    this.messageField = messageField;
    this.progress = ref(0);
    this.message = ref('');
    this.isDone = computed(() => this.progress.value >= 100)
    this.startTime = null;
  }

  start() {
    this.startTime = new Date();
    this.fetchProgress();
  }

  fetchProgress = () => {
    fetch(this.url)
      .then(response => response.json())
      .then(data => {
        console.log(data);
        this.progress.value = data[this.progressField];
        
        if (this.messageField) {
          this.message.value = data[this.messageField];
        }
        if (this.progress < 100) {
          setTimeout(this.fetchProgress, 10000)
        }
      });
  }
}


const activeLongProcess = ref(new LongProcess());
const showActiveLongProcess = ref(false);

export function useLongProcessState() {
  const toggleShowActiveLongProcess = () => showActiveLongProcess.value = !showActiveLongProcess.value;

  const startLongProcess = (name, url, requestParams, progress_field, message_field) => {
    activeLongProcess.value = new LongProcess(name, url, requestParams, progress_field, message_field);
    showActiveLongProcess.value = true;
    activeLongProcess.value.start();

    watchEffect(() => {
      if (activeLongProcess.value.progress >= 100) {
        // TODO: Implement done callback.
      }
    });
  }


  return {
    activeLongProcess,
    toggleShowActiveLongProcess,
    showActiveLongProcess,
    startLongProcess,
  }
}
