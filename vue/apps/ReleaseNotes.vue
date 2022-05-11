<template>
  <a class="dropdown-item" href="#" @click="showReleaseNotes">
    <div id="menu_doc" class="menu-icon" style="margin-top:0px"><i class="fa fa-info-circle" aria-hidden="true" /></div>
    Release notes...
  </a>
  <a-modal v-model:visible="visibleReleaseNotes" :title="'Release notes - version ' + current_release_notes.version" width="750px">
    <template #footer>
      <a-button
        v-if="current_release_notes_index < release_notes_info.length - 1"
        key="previous"
        @click="previous_release_notes"
      >
        Previous
      </a-button>

      <a-button
        v-if="current_release_notes_index == 0"
        key="ok"
        type="primary"
        @click="hideReleaseNotes"
      >
        Ok
      </a-button>
      <a-button
        v-else
        key="next"
        type="primary"
        @click="next_release_notes"
      >
        Next
      </a-button>
    </template>
    <div style="overflow-y:auto; height: 450px;">
      <p>
        {{ current_release_notes.general_message }}
      </p>

      <template
        v-for="cat in current_release_notes.categories"
        :key="cat.version"
      >
        <h2>{{ cat.name }}</h2>
        <ul>
          <li
            v-for="item in cat.items"
            :key="item"
          >
            {{ item }}
          </li>
        </ul>
      </template>
    </div>
  </a-modal>
</template>

<script>
import { useReleaseNotes } from "../composables/releaseNotes";

const { visibleReleaseNotes, releaseNotesData, getReleaseNotesData, showReleaseNotes, hideReleaseNotes } =
  useReleaseNotes();

export default {
  name: "ReleaseNotes",
  setup() {
    return {
      visibleReleaseNotes,
      showReleaseNotes,
      hideReleaseNotes
    }
  },
  data() {
    return {
      release_notes_info: [],
      latest_seen: "",
      current_shown_version: "",
      current_release_notes_index: 0,
      current_release_notes: {}
    }
  },
  mounted() {
    this.get_release_notes();
  },
  methods: {
    async get_release_notes() {
      await getReleaseNotesData();

      if (releaseNotesData.value) {
        this.release_notes_info = releaseNotesData.value.release_notes;
        this.latest_seen = releaseNotesData.value.latest_seen;
        if (this.latest_seen == "") {
          // show only latest release notes when user never saw release notes before
          this.current_release_notes_index = 0;
        } else {
          // show only the release notes of the newer release if the user already saw release notes
          for (let i=0; i<this.release_notes_info.length - 1; i++) {
            if (this.release_notes_info[i+1].version == this.latest_seen) {
              this.current_release_notes_index = i;
              break;
            }
          }
        }
        this.current_release_notes = this.release_notes_info[this.current_release_notes_index];

        if (this.release_notes_info[0].version == this.latest_seen) {
          // latest release notes have been shown already
          visibleReleaseNotes.value = false;
        } else {
          visibleReleaseNotes.value = true;
        }
      }
    },
    next_release_notes() {
      this.current_release_notes_index -= 1;
      this.current_release_notes = this.release_notes_info[this.current_release_notes_index];
    },
    previous_release_notes() {
      this.current_release_notes_index += 1;
      this.current_release_notes = this.release_notes_info[this.current_release_notes_index];
    }
  },
};

</script>