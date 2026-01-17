rs.initiate({
  _id: "shard0",
  version: 1,
  members: [
    { _id: 0, host: "172.16.17.20:27018" },
    { _id: 1, host: "172.16.17.21:27018" },
  ],
});
