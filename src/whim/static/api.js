class APIClient {
  call(method, payload) {
    let promise = new Promise(function(resolve, reject) {
      let xhr = new XMLHttpRequest();

      xhr.onreadystatechange = function () {
        if (this.readyState != 4) return;

        if (this.status == 200) {
          let data = JSON.parse(this.responseText);
          resolve(data);
        } else {
          reject();
        }
      };

      xhr.open('POST', '/api/' + method, true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.send(JSON.stringify(payload));
    });

    return promise;
  }

  async readFile(file_path) {
    return (await this.call('read_file', {
      file_path: file_path
    })).file_content;
  }

  async writeFile(file_path, file_content) {
    return await this.call('write_file', {
      file_path: file_path,
      file_content: file_content
    });
  }
}
