rs.initiate({
  _id: "mongodb-action-replica-set",
  version: 1,
  members: [
    { _id: 0, host: "172.16.17.11:27017" },
    { _id: 1, host: "172.16.17.12:27017" },
    { _id: 2, host: "172.16.17.13:27017" },
  ],
});
