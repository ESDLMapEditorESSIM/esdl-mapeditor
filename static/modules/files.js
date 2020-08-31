
/**
 * Make the browser download a binary file that is base64 encoded
 * @param {*} base64_str The contents of the file.
 * @param {*} file_name The name of the file, as offered to the user.
 */
export function download_binary_file_from_base64_str(base64_str, file_name) {
    download_binary_file_from_base64_str_with_type(base64_str, file_name, 'application/octet-stream');
}

export function download_binary_file_from_base64_str_with_type(base64_str, file_name, content_type) {
    const byte_array = base64_str_to_byte_array(base64_str)
    const blob = new Blob([byte_array], { 'type': content_type });
    const a = document.createElement('a');
    const url = window.URL.createObjectURL(blob);
    a.href = url;
    a.download = file_name;
    a.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Turn a base64 encoded string back into a binary array. For details see:
 * http://stackoverflow.com/questions/16245767/creating-a-blob-from-a-base64-string-in-javascript
 * @param {*} base64_str 
 */
export function base64_str_to_byte_array(base64_str) {
    const byteCharacters = atob(base64_str);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    return new Uint8Array(byteNumbers);
}