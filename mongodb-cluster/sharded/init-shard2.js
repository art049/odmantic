rs.initiate({
  _id: "shard2",
  version: 1,
  members: [
    { _id: 0, host: "172.16.17.40:27018" },
    { _id: 1, host: "172.16.17.41:27018" },
  ],
});
