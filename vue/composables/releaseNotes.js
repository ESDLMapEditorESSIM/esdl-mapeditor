import { ref, reactive } from "vue";

const visibleReleaseNotes = ref(false);
const releaseNotesData = reactive({});

export function useReleaseNotes() {

  const queryReleaseNotes = async () => {
    const path = '/get_release_notes';
    try {
      const response = await fetch(path);
      return response.json();
    } catch (e) {
      // eslint-disable-next-line
      console.error(error);
      return null;
    }
  }

  const getReleaseNotesData = async () => {
    if (!releaseNotesData.value) {
      try {
        const data = await queryReleaseNotes();
        releaseNotesData.value = data;
      } catch (e) {
        console.error(e);
        releaseNotesData.value = null
      }
    }
  }

  const showReleaseNotes = () => {
    visibleReleaseNotes.value = true;
  }

  const hideReleaseNotes = () => {
    visibleReleaseNotes.value = false;
  }

  return {
    visibleReleaseNotes,
    releaseNotesData,
    getReleaseNotesData,
    showReleaseNotes,
    hideReleaseNotes,
  }
}
