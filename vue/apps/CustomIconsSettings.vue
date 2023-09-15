<template>
  <h1>Custom icons</h1>
  <a-space
    direction="vertical"
  >
    <a-table
      :columns="columns"
      :data-source="icons_list"
      row-key="id"
      :pagination="{ pageSize: 5 }"
    >
      <template #icon_draw="{ record }">
        <span>
          <img
            v-if="record.icon"
            width="32"
            :src="'data:' + record.icon.content_type + ';base64,' + record.icon.data"
          />
        </span>
      </template>
    </a-table>

    <a-input
      v-model:value="selector"
      size="small"
      type="text"
    />

    <a-upload
      v-model:file-list="image_files"
      name="file"
      :multiple="false"
      action=""
      :headers="headers_image"
      @change="handleChangeImage"
      :before-upload="beforeImageUpload"
    >
      <a-space>
        <a-button>
          <upload-outlined></upload-outlined>
          Click to Upload
        </a-button>
        <a-spin
          v-if="is_image_loading"
        />
      </a-space>
    </a-upload>
    <img
      v-if="custom_icon"
      :src="'data:' + custom_icon.contentType + ';base64,' + custom_icon.imageData"
    />

    <a-button
      type="primary"
      :disabled="!custom_icon || !selector"
      @click="add_icon"
    >
      Add icon
    </a-button>
  </a-space>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { UploadOutlined } from '@ant-design/icons-vue';
import spinner from "../components/Spinner.vue";
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

const isLoading = ref(true);
const selector = ref("");
const icons_list = ref([]);

const columns = [
  {
    title: 'Asset class',
    dataIndex: 'selector',
    width: 500,
  },
  {
    title: 'Icon',
    dataIndex: 'icon',
    slots: { customRender: 'icon_draw' }
  }
];

function get_custom_icons() {
  const path = '/custom_icons';
  axios.get(path)
    .then((res) => {
      console.log(res);
      icons_list.value = res.data.icons_list;
    })
    .catch((error) => {
      // eslint-disable-next-line
      console.error(error);
    });
}
get_custom_icons();

function add_icon() {
  console.log('icon must be added');
  if (custom_icon.value && selector.value) {
    axios.post('/custom_icon', {
      id: uuidv4(),
      asset_selector: selector.value,
      image_content_type: custom_icon.value.contentType,
      image_data: custom_icon.value.imageData
    })
      .then((res) => {
        console.log('POST successful')
      })
      .catch((error) => {
        // eslint-disable-next-line
        console.error(error);
      });
  }
}

// =================================================================================================================
//  Upload image functionality
// =================================================================================================================
// eslint-disable-next-line
const image_files = ref([]);
const is_image_loading = ref(false);
const custom_icon = ref(null);

// eslint-disable-next-line
const handleChangeImage = (info) => {
  if (info.file.status !== 'uploading') {
    console.log(info.file, info.fileList);
  }

  if (info.file.status === 'done') {
    console.log(`${info.file.name} file uploaded successfully`);
  } else if (info.file.status === 'error') {
    console.log(`${info.file.name} file upload failed.`);
  }
};

// eslint-disable-next-line
const headers_image = reactive({
    authorization: 'authorization-text',
});

// eslint-disable-next-line
const beforeImageUpload = file => {
  if (file.size > 8000) {
    console.log("File size too big!")
    return true;
  }

  return new Promise(() => {
    is_image_loading.value = true;
    const reader = new FileReader();
    reader.readAsDataURL(file);

    reader.onload = () => {
      let res = reader.result;
      // eslint-disable-next-line
      let [content_type, data] = res.split(',')
      if (custom_icon.value && 'imageData' in custom_icon.value) {
        custom_icon.value.contentType = content_type;
        custom_icon.value.imageData = data;
      } else {
        custom_icon.value = {
          contentType: content_type.split(';')[0],
          imageData: data,
        };
      }
      is_image_loading.value = false;
    };

    return false;
  });
}

</script>

<style>
</style>
