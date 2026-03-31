<template>
  <div class="code-editor-wrapper">
    <div
      ref="editorContainer"
      class="code-editor"
      :class="{ 'code-editor--error': error }"
      :style="{ height: (2 + nrOfRows * 1.4) + 'em' }"
    />

    <div v-if="error" class="error">
      {{ language }}: {{ error }}
    </div>
    <div v-else class="valid">
      {{ language }}
    </div>
  </div>
</template>

<script setup>
import {ref, onUnmounted, watch, computed} from 'vue';
import {EditorState} from '@codemirror/state';
import {EditorView, keymap, lineNumbers} from '@codemirror/view';
import {defaultKeymap, history} from '@codemirror/commands';
import {oneDark} from '@codemirror/theme-one-dark';

import {json} from '@codemirror/lang-json';
import {yaml} from '@codemirror/lang-yaml';
import {xml} from '@codemirror/lang-xml';
import {python} from '@codemirror/lang-python';
import {markdown} from '@codemirror/lang-markdown';

import prettier from 'prettier/standalone';
import parserBabel from 'prettier/plugins/babel';
import parserHtml from 'prettier/plugins/html';
import parserEstree from 'prettier/plugins/estree';
import YAML from 'js-yaml';
import {XMLParser} from 'fast-xml-parser';

const props = defineProps({
  modelValue: {type: [String, Object], default: ''},
  language: {type: String, default: 'json'},
  nrOfRows: {type: Number, default: 20},
  updateOnInput: {type: Boolean, default: false},
  formatOnBlur: {type: Boolean, default: true},
});

const emit = defineEmits(['update:modelValue', 'change', 'validate', 'blur']);

const editorContainer = ref(null);
const error = ref(null);
let editorView = null;

const xmlParser = new XMLParser({ignoreAttributes: false});

const LANGUAGES = {
  json: {
    extension: json(),
    parse: (v) => JSON.parse(v),
    format: (v) => prettier.format(v, {parser: 'json', plugins: [parserBabel, parserEstree]})
  },
  yaml: {
    extension: yaml(),
    parse: (v) => YAML.load(v),
    format: (v) => YAML.dump(YAML.load(v), {indent: 2}),
  },
  xml: {
    extension: xml(),
    parse: (v) => xmlParser.parse(v),  // TODO more strict parser
    format: (v) =>
        prettier.format(v, {parser: 'html', plugins: [parserHtml]}),
  },
  python: {
    extension: python(),
    parse: (v) => v,  // TODO parser
    format: (v) => v,
  },
  markdown: {
    extension: markdown(),
    parse: (v) => v,  // TODO parser
    format: (v) => v,
  },
};

const currentLang = computed(() => LANGUAGES[props.language] || LANGUAGES.json);

// on update emit validate and optionally update v-model
const onUpdate = (value) => {
  try {
    currentLang.value.parse(value); // syntax check
    error.value = null;
    emit('validate', {valid: true});

    // optional live update
    if (props.emitOnInput) {
      emit('update:modelValue', value);
    }

    return true;
  } catch (e) {
    error.value = e.message || 'Invalid content';
    emit('validate', {valid: false, error: error.value});
    return false;
  }
};


// on blur parse, format and emit
const handleBlur = async () => {
  const value = editorView.state.doc.toString();

  try {
    currentLang.value.parse(value);

    if (props.formatOnBlur && currentLang.value.format) {
      const formatted = await currentLang.value.format(value);
      if (formatted !== value) {
        editorView.dispatch({
          changes: {from: 0, to: value.length, insert: formatted},
        });
      }
    }

    error.value = null;

    emit('update:modelValue', editorView.state.doc.toString());
    emit('change', editorView.state.doc.toString());
    emit('blur', editorView.state.doc.toString());
  } catch (e) {
    error.value = e.message || 'Invalid content';
    emit('validate', {valid: false, error: error.value});
  }
};

const createEditor = (initialValue) => {
  editorView = new EditorView({
    state: EditorState.create({
      doc: initialValue,
      extensions: [
        lineNumbers(),
        keymap.of(defaultKeymap),
        history(),
        currentLang.value.extension,
        oneDark,
        EditorView.updateListener.of((update) => {
          if (!update.docChanged) return;
          onUpdate(update.state.doc.toString());
        }),
        EditorView.domEventHandlers({
          blur: handleBlur,
        }),
      ],
    }),
    parent: editorContainer.value,
  });
};

// only create after language is set
watch(
  () => props.language,
  (lang) => {
    if (!lang || editorView) return; // only create once
    const initialValue = typeof props.modelValue === 'string'
      ? props.modelValue
      : JSON.stringify(props.modelValue ?? {}, null, 2);
    createEditor(initialValue);
  },
  { immediate: true }
);

watch(
    () => props.modelValue,
    (newVal) => {
      if (!editorView) return;

      const current = editorView.state.doc.toString();

      if (current === newVal) return;

      editorView.dispatch({changes: {from: 0, to: current.length, insert: newVal}});
    }
);

onUnmounted(() => {
  if (editorView) editorView.destroy();
});

defineExpose({
  validate: () => onUpdate(editorView.state.doc.toString()),

  getValue: () => editorView.state.doc.toString(),

  setValue: (val) =>
      editorView.dispatch({
        changes: {from: 0, to: editorView.state.doc.length, insert: val},
      }),
});
</script>

<style scoped>
.code-editor {
  font-family: monospace;
  border: 1px solid #4caf50;
  transition: border-color 0.15s ease;
  padding: 4px;
  resize: vertical;
  overflow: hidden;
}

.code-editor--error {
  border-color: #d32f2f;
}

.valid {
  color: #4caf50;
  margin-top: 4px;
}

.error {
  color: #d32f2f;
  margin-top: 4px;
}

.code-editor :deep(.cm-editor) {
  height: 100%;
}

.code-editor :deep(.cm-scroller) {
  height: 100%;
  overflow: auto;
}
</style>
