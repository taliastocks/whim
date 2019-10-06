function asyncConfirm(message) {
  return new Promise((resolve) => {
    alertify.confirm(
      'Confirm',
      message,
      () => {
        resolve(true);
      },
      () => {
        resolve(false);
      }
    ).set({
      transition: 'fade'
    });
  });
}
