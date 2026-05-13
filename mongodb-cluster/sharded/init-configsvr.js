rs.initiate({
  _id: "config-rs",
  configsvr: true,
  version: 1,
  members: [{ _id: 0, host: "172.16.17.11:27019" }],
});
