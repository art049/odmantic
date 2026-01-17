rs.initiate({
  _id: "shard1",
  version: 1,
  members: [
    { _id: 0, host: "172.16.17.30:27018" },
    { _id: 1, host: "172.16.17.31:27018" },
  ],
});
