import json
invest_abi = json.loads('''[
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "Breach",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "BurnCertificae",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "address",
				"name": "_investor",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "BuyTranche",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			}
		],
		"name": "EarlyPayback",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "LoanEnded",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "LoanPassed",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "address",
				"name": "_borrow_company",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_principle",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_interest",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_datespan",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_riskClass",
				"type": "uint256"
			}
		],
		"name": "MintCertificate",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			}
		],
		"name": "NormalPayback",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_term",
				"type": "uint256"
			}
		],
		"name": "allocateDividend",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "breach",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "burnCertificate",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_investor",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "buyTranche",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "certificateMapping",
		"outputs": [
			{
				"internalType": "address",
				"name": "borrow_company",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "principle",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "interest",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "dateSpan",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "riskClass",
				"type": "uint256"
			},
			{
				"internalType": "enum investmentToken.State",
				"name": "state",
				"type": "uint8"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "classPayback",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_principle",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_interest",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_datespan",
				"type": "uint256"
			}
		],
		"name": "createInterestArray",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "decimals",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "earlyPayback",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "earlyUpdateInterestArr",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "getClassDividendNotPaid",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "getClassPrincipleNotPaid",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_index",
				"type": "uint256"
			}
		],
		"name": "getInterestArrValue",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_investor",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			}
		],
		"name": "getInvestorLoanIdClassList",
		"outputs": [
			{
				"internalType": "uint256[]",
				"name": "",
				"type": "uint256[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_investor",
				"type": "address"
			}
		],
		"name": "getInvestorLoanIdList",
		"outputs": [
			{
				"internalType": "uint256[]",
				"name": "",
				"type": "uint256[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_investor",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "getInvestorTrancheAmount",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "getPaidTrancheNum",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_index",
				"type": "uint256"
			}
		],
		"name": "getPrincipleArrValue",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_term",
				"type": "uint256"
			}
		],
		"name": "getTermIntPayable",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_investor",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_term",
				"type": "uint256"
			}
		],
		"name": "getTermInvestorDiv",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_term",
				"type": "uint256"
			}
		],
		"name": "getTermPriPayable",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "getTotalClassIntPayable",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			}
		],
		"name": "getTotalPrincipleNotPaid",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_investor",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "getTrancheByInvestor",
		"outputs": [
			{
				"components": [
					{
						"internalType": "uint256",
						"name": "amount",
						"type": "uint256"
					},
					{
						"internalType": "uint256[]",
						"name": "dividendIncome",
						"type": "uint256[]"
					},
					{
						"internalType": "uint256",
						"name": "riskClass",
						"type": "uint256"
					}
				],
				"internalType": "struct investmentToken.TrancheInv",
				"name": "",
				"type": "tuple"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "getTrancheState",
		"outputs": [
			{
				"internalType": "enum investmentToken.State",
				"name": "",
				"type": "uint8"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "interestRecMapping",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "dateSpan",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "termLeft",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "interest",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "investorTranche",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "amount",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "riskClass",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "loanEnded",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "loanPassed",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "address",
				"name": "_borrow_company",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "_principle",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_interest",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_datespan",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			}
		],
		"name": "mintCertificate",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "normalPayback",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "payback",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "paybackDividend",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "address",
				"name": "_investor",
				"type": "address"
			}
		],
		"name": "trancheAddInvestor",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "index",
				"type": "uint256"
			}
		],
		"name": "trancheGetInvestor",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_loan_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_class",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "updateInterestArr",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]''')